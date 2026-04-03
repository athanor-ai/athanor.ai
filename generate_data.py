#!/usr/bin/env python3
"""Generate CALIBRATOR_DATA for the Athanor website from env repo run files.

Reads run results from all 6 environment repos and produces a data.js file
that the website imports. Run after shipping envs or updating scores.

Usage:
    python3 generate_data.py                    # auto-detect env dirs
    python3 generate_data.py --output data.js   # custom output
    python3 generate_data.py --envs-dir /path   # custom env location
"""

import argparse
import json
import glob
import os
from pathlib import Path

# Model order: strongest to weakest (by overall mean across all envs)
MODELS = [
    "claude-sonnet-4-6",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
    "mistral-large-3",
    "kimi-k2.5",
]

MODEL_DISPLAY = {
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "kimi-k2.5": "Kimi K2.5",
    "mistral-large-3": "Mistral Large 3",
}

# Env metadata (order, display name, description)
ENVS = [
    {
        "dir": "hw-cbmc-env",
        "id": "hw-cbmc",
        "name": "Hardware Verification",
        "desc": "Agents debug and formally verify hardware designs against temporal and safety properties.",
    },
    {
        "dir": "lean-demo",
        "id": "lean",
        "name": "Theorem Proving",
        "desc": "Agents construct formal proofs covering compiler correctness, data structure invariants, and abstract algebra.",
    },
    {
        "dir": "csparse-rust-env",
        "id": "csparse",
        "name": "Systems Migration",
        "desc": "Agents port numerical computing libraries to a memory-safe language with formal verification.",
    },
    {
        "dir": "congestion-control",
        "id": "congestion",
        "name": "Network Protocols",
        "desc": "Agents implement and fix congestion control algorithms, verified against performance and fairness targets.",
    },
    {
        "dir": "distributed-consensus",
        "id": "consensus",
        "name": "Distributed Systems",
        "desc": "Agents build and repair consensus protocols, verified against safety and liveness specifications.",
    },
    {
        "dir": "cedar-env",
        "id": "cedar",
        "name": "Authorization",
        "desc": "Agents write and verify authorization policies against security property specifications.",
    },
]

# Task display name cleanup
def task_display_name(task_id: str) -> str:
    """Convert task ID to vague human-readable name (hide tool specifics)."""
    name = task_id.replace("-", " ").replace("_", " ")
    # Strip tool-revealing prefixes
    for prefix in ["write assertions ", "verify ", "verus ", "csparse ", "csc "]:
        if name.lower().startswith(prefix):
            name = name[len(prefix):]
    # Capitalize
    words = name.split()
    result = []
    for w in words:
        if w.lower() in ("fifo", "uart", "spi", "i2c", "dma", "alu", "axi", "tlb",
                          "arb", "lfsr", "irq", "bft", "pbft", "crdt", "lsm",
                          "bbr", "aimd", "pcc", "tcp"):
            result.append(w.upper())
        else:
            result.append(w.capitalize())
    return " ".join(result)


def task_description(task_id: str, config: dict, env_id: str) -> str:
    """Generate vague, high-level descriptions that don't reveal tools or methods."""
    tt = config.get("task_type", "")

    # Formal verification tasks -- keep vague
    if any(kw in tt for kw in ["assertion", "verify", "verus", "formal", "fill_sorry", "fix_broken"]):
        return "Write formal proofs that a verifier accepts."

    # Domain-specific but vague
    if env_id == "hw-cbmc":
        return "Debug or verify a hardware design against formal properties."
    if env_id == "consensus":
        if "fix" in tt: return "Fix bugs in a distributed protocol implementation."
        return "Implement a distributed protocol from specification."
    if env_id == "congestion":
        if "fix" in tt: return "Fix a network protocol to meet performance targets."
        if "implement" in tt: return "Implement a network protocol from scratch."
        return "Optimize network protocol parameters."
    if env_id == "csparse":
        return "Port a numerical computing function to a verified implementation."
    if env_id == "cedar":
        if "fix" in tt: return "Fix bugs in an authorization policy system."
        return "Build or verify authorization policies."
    if env_id == "lean":
        return "Construct formal mathematical proofs."

    return "Complete the engineering task."


def load_scores(env_dir: Path) -> dict:
    """Load best scores per task per model from run files."""
    scores = {}  # {task: {model: score}}
    runs_dir = env_dir / "runs"
    if not runs_dir.exists():
        return scores

    for run_file in sorted(runs_dir.glob("*_run*.json")):
        try:
            data = json.loads(run_file.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        # Extract model name from filename (e.g., "claude-sonnet-4-6_run1.json")
        model = run_file.stem.rsplit("_run", 1)[0]

        for result in data.get("results", []):
            task = result.get("task", "")
            # Normalize: hyphens -> underscores (canonical form)
            task = task.replace("-", "_")
            score = result.get("score")
            if score is None:
                continue
            # Keep best score across runs
            if task not in scores:
                scores[task] = {}
            if model not in scores[task] or score > scores[task][model]:
                scores[task][model] = score

    return scores


def load_configs(env_dir: Path) -> dict:
    """Load all task configs."""
    configs = {}
    configs_dir = env_dir / "root_data" / "eval" / "configs"
    if not configs_dir.exists():
        return configs
    for f in sorted(configs_dir.glob("*.json")):
        try:
            configs[f.stem] = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return configs


def _select_showcase_tasks(tasks: list, n: int = 3) -> list:
    """Select n tasks for the website showcase.

    Hard requirements:
    - ALL 5 model scores must be non-None (no empty boxes ever)
    - Model spread > 0.1 (boring if all models score the same)

    Criteria (in priority order):
    1. Sonnet leads or ties for best score (shows our primary model well)
    2. Good difficulty spread across models (interesting to look at)
    3. Mix of difficulty levels (hard/medium/easy)
    """
    def sonnet_score(t):
        return t["f"][0] if t["f"][0] is not None else -1

    def sonnet_leads(t):
        s = sonnet_score(t)
        if s < 0: return False
        others = [x for x in t["f"][1:] if x is not None]
        if not others: return True
        return s >= max(others) - 0.05

    def model_spread(t):
        valid = [s for s in t["f"] if s is not None]
        if len(valid) < 2: return 0
        return max(valid) - min(valid)

    # Hard filter: all 5 scores present + some spread
    tasks = [t for t in tasks if all(s is not None for s in t["f"])]
    tasks = [t for t in tasks if model_spread(t) > 0.1]

    if len(tasks) <= n:
        return tasks

    # Prefer tasks where Sonnet leads
    sonnet_wins = [t for t in tasks if sonnet_leads(t)]
    sonnet_loses = [t for t in tasks if not sonnet_leads(t)]

    # Within each group, sort by spread (more interesting)
    sonnet_wins.sort(key=model_spread, reverse=True)
    sonnet_loses.sort(key=model_spread, reverse=True)

    # Build from Sonnet-winning tasks first, fill from others
    pool = sonnet_wins + sonnet_loses

    # Pick for difficulty spread: one hard, one medium, one easy
    hard = [t for t in pool if sonnet_score(t) < 0.4]
    medium = [t for t in pool if 0.4 <= sonnet_score(t) <= 0.75]
    easy = [t for t in pool if sonnet_score(t) > 0.75]

    selected = []
    for bucket in [hard, medium, easy]:
        if bucket and len(selected) < n:
            selected.append(bucket[0])

    # Fill remaining from pool (Sonnet-wins first)
    remaining = [t for t in pool if t not in selected]
    while len(selected) < n and remaining:
        selected.append(remaining.pop(0))

    # Sort: easiest on top (highest Sonnet score), hardest on bottom
    selected.sort(key=lambda t: -(t["f"][0] if t["f"][0] is not None else 0))

    return selected


def generate_data(envs_dir: Path) -> dict:
    """Generate the full CALIBRATOR_DATA structure."""
    output = {
        "models": MODELS,
        "modelNames": MODEL_DISPLAY,
        "envs": [],
    }

    for env_meta in ENVS:
        env_dir = envs_dir / env_meta["dir"]
        if not env_dir.exists():
            print(f"  SKIP: {env_meta['dir']} not found")
            continue

        configs = load_configs(env_dir)
        scores = load_scores(env_dir)

        tasks = []
        for task_id in sorted(configs.keys()):
            # Check both hyphen and underscore variants (envs are inconsistent)
            task_id_alt = task_id.replace("_", "-") if "_" in task_id else task_id.replace("-", "_")
            config = configs[task_id]
            scoring = config.get("scoring", {})
            center = scoring.get("sigmoid_center", 0.5)
            scale = scoring.get("sigmoid_scale", 8.0)

            # Build score array in model order (check both hyphen and underscore variants)
            task_scores = scores.get(task_id, scores.get(task_id_alt, {}))
            f = []
            for model in MODELS:
                s = task_scores.get(model)
                f.append(round(s, 4) if s is not None else None)

            # Skip tasks with ANY missing model scores (no empty boxes on website)
            if any(s is None for s in f):
                continue

            tasks.append({
                "n": task_display_name(task_id),
                "d": task_description(task_id, config, env_meta["id"]),
                "c": center,
                "s": scale,
                "f": f,
            })

        # Select 3 best tasks: pick for maximum difficulty spread
        # (one easy, one medium, one hard based on Sonnet score)
        selected = _select_showcase_tasks(tasks, n=3)

        env_data = {
            "id": env_meta["id"],
            "name": env_meta["name"],
            "desc": env_meta["desc"],
            "tasks": selected,
        }
        output["envs"].append(env_data)
        print(f"  {env_meta['id']}: {len(selected)}/{len(tasks)} tasks selected")

    return output


def main():
    parser = argparse.ArgumentParser(description="Generate website data from env repos")
    parser.add_argument("--envs-dir", default=str(Path.home()),
                        help="Directory containing env repos (default: ~)")
    parser.add_argument("--output", default="data.js",
                        help="Output file (default: data.js)")
    parser.add_argument("--json", action="store_true",
                        help="Output raw JSON instead of JS const")
    args = parser.parse_args()

    envs_dir = Path(args.envs_dir)
    print(f"Generating website data from {envs_dir}...")

    data = generate_data(envs_dir)

    if args.json:
        output = json.dumps(data, indent=2)
    else:
        # Output as JS const that index.html can import
        output = f"// Auto-generated by generate_data.py -- do not edit manually\n"
        output += f"// Generated from env repos at {envs_dir}\n"
        output += f"const CALIBRATOR_DATA = {json.dumps(data, indent=2)};\n"

    Path(args.output).write_text(output)

    total_tasks = sum(len(e["tasks"]) for e in data["envs"])
    total_scored = sum(
        1 for e in data["envs"]
        for t in e["tasks"]
        if any(s is not None for s in t["f"])
    )
    print(f"\nOutput: {args.output}")
    print(f"Total: {total_tasks} tasks, {total_scored} with scores, {len(data['envs'])} envs")


if __name__ == "__main__":
    main()
