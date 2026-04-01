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
    "Mistral-large-3",
    "kimi-k2.5",
]

MODEL_DISPLAY = {
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "kimi-k2.5": "Kimi K2.5",
    "Mistral-large-3": "Mistral Large 3",
}

# Env metadata (order, display name, description)
ENVS = [
    {
        "dir": "hw-cbmc-env",
        "id": "hw-cbmc",
        "name": "Hardware Verification",
        "desc": "Agents fix bugs in SystemVerilog designs and write formal assertions, verified by EBMC bounded model checker.",
    },
    {
        "dir": "lean-demo",
        "id": "lean",
        "name": "Theorem Proving",
        "desc": "Agents construct formal proofs in Lean 4 covering compiler correctness, data structure invariants, and rewriting systems.",
    },
    {
        "dir": "csparse-rust-env",
        "id": "csparse",
        "name": "Systems Migration",
        "desc": "Agents migrate C sparse matrix libraries to idiomatic Rust with Verus verification annotations.",
    },
    {
        "dir": "congestion-control",
        "id": "congestion",
        "name": "Congestion Control",
        "desc": "Agents implement and fix TCP congestion control algorithms with Dafny formal verification of protocol safety.",
    },
    {
        "dir": "distributed-consensus",
        "id": "consensus",
        "name": "Distributed Systems",
        "desc": "Agents build and repair distributed consensus protocols with Dafny proofs of safety properties.",
    },
    {
        "dir": "cedar-env",
        "id": "cedar",
        "name": "Authorization",
        "desc": "Agents write Cedar authorization policies and prove security properties in Lean 4.",
    },
]

# Task display name cleanup
def task_display_name(task_id: str) -> str:
    """Convert task ID to human-readable name."""
    name = task_id.replace("-", " ").replace("_", " ")
    # Capitalize each word, handle special cases
    words = name.split()
    result = []
    for w in words:
        if w.lower() in ("fifo", "uart", "spi", "i2c", "dma", "alu", "axi", "tlb",
                          "arb", "lfsr", "noc", "smv", "irq", "bft", "pbft", "crdt",
                          "lsm", "bbr", "aimd", "pcc", "tcp", "rbt", "sva", "ebmc"):
            result.append(w.upper())
        elif w.lower() in ("fix", "implement", "write", "verify", "prove", "verus"):
            result.append(w.capitalize())
        else:
            result.append(w.capitalize())
    return " ".join(result)


def task_description(task_id: str, config: dict, env_id: str) -> str:
    """Generate a meaningful description from task ID, config, and env context."""
    tt = config.get("task_type", "")
    name = task_id.replace("-", " ").replace("_", " ")

    # Formal verification tasks -- specific per verifier
    if "assertion" in tt or "write_assertion" in tt:
        return f"Write SVA assertions for a {name.replace('write assertions ', '')} module and verify with EBMC."
    if "verify" in tt or "formal" in tt:
        subject = name.replace("verify ", "")
        return f"Prove {subject} safety properties in Dafny."
    if "verus" in tt:
        subject = name.replace("verus ", "").replace(" proof", "")
        return f"Add Verus verification annotations to prove {subject} operations correct."
    if "fill_sorry" in tt:
        subject = name.replace("fix proof errors", "proof repair").replace("fix wrong lemma", "lemma repair")
        return f"Construct Lean 4 proofs for {subject}."

    # Domain-specific descriptions
    if env_id == "hw-cbmc":
        if "fix" in tt:
            circuit = name.replace("fix ", "")
            return f"Debug a {circuit} circuit until all formal properties prove."
        return f"Implement a {name.replace('implement ', '')} circuit to satisfy formal properties."

    if env_id == "consensus":
        if "fix" in tt:
            protocol = name.replace("fix ", "")
            return f"Fix bugs in a {protocol} protocol implementation."
        return f"Implement {name.replace('implement ', '')} from the protocol specification."

    if env_id == "congestion":
        if "fix" in tt:
            algo = name.replace("fix ", "")
            return f"Fix {algo} congestion control to meet throughput and fairness targets."
        if "implement" in tt:
            algo = name.replace("implement ", "")
            return f"Implement {algo} congestion control from scratch."
        if "tune" in tt:
            return f"Tune {name.replace('tune ', '')} parameters for target network conditions."
        return f"Complete the {name} congestion control task."

    if env_id == "csparse":
        subject = name.replace("csparse ", "")
        return f"Port the CSparse {subject} function from C to idiomatic Rust."

    if env_id == "cedar":
        if "fix" in tt:
            return f"Fix authorization policy bugs in {name.replace('fix ', '')}."
        if "prove" in name.lower():
            subject = name.replace("prove ", "")
            return f"Prove {subject} in Lean 4."
        return f"Build authorization policies for {name.replace('implement ', '')}."

    return f"Complete the {name} task."


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

    Criteria (in priority order):
    1. Sonnet leads or ties for best score (shows our primary model well)
    2. Good difficulty spread across models (interesting to look at)
    3. Mix of difficulty levels (hard/medium/easy)
    """
    if len(tasks) <= n:
        return tasks

    def sonnet_score(t):
        return t["f"][0] if t["f"][0] is not None else -1

    def sonnet_leads(t):
        """True if Sonnet is the best or tied-best model on this task."""
        s = sonnet_score(t)
        if s < 0:
            return False
        others = [x for x in t["f"][1:] if x is not None]
        if not others:
            return True
        return s >= max(others) - 0.05  # within 0.05 counts as tied

    def model_spread(t):
        valid = [s for s in t["f"] if s is not None]
        if len(valid) < 2:
            return 0
        return max(valid) - min(valid)

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
            config = configs[task_id]
            scoring = config.get("scoring", {})
            center = scoring.get("sigmoid_center", 0.5)
            scale = scoring.get("sigmoid_scale", 8.0)

            # Build score array in model order
            task_scores = scores.get(task_id, {})
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
