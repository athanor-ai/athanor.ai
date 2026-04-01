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

# Model order (matches website display)
MODELS = [
    "claude-sonnet-4-6",
    "gemini-2.5-flash",
    "gemini-3.1-pro-preview",
    "kimi-k2.5",
    "Mistral-large-3",
]

MODEL_DISPLAY = {
    "claude-sonnet-4-6": "Claude Sonnet 4",
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


def task_description(task_id: str, config: dict) -> str:
    """Generate a short description from task config."""
    tt = config.get("task_type", "")
    if "assertion" in tt or "write_assertion" in tt:
        return "Write formal SVA assertions to verify hardware correctness properties."
    if "verify" in tt or "formal" in tt:
        return "Fill in formal proof obligations so the verifier accepts."
    if "verus" in tt:
        return "Add Verus verification annotations to prove Rust code correct."
    if "fill_sorry" in tt:
        return "Replace sorry placeholders with valid Lean 4 proofs."
    if "fix" in tt:
        return "Find and fix bugs in the implementation until all tests pass."
    if "implement" in tt:
        return "Implement the algorithm from scratch to meet the specification."
    if "tune" in tt:
        return "Tune parameters to optimize performance on target workloads."
    return "Complete the task to pass the automated evaluation."


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

            # Skip tasks with fewer than 2 model scores (looks bad on website)
            scored_count = sum(1 for s in f if s is not None)
            if scored_count < 2:
                continue

            tasks.append({
                "n": task_display_name(task_id),
                "d": task_description(task_id, config),
                "c": center,
                "s": scale,
                "f": f,
            })

        env_data = {
            "id": env_meta["id"],
            "name": env_meta["name"],
            "desc": env_meta["desc"],
            "tasks": tasks,
        }
        output["envs"].append(env_data)
        scored = sum(1 for t in tasks if any(s is not None for s in t["f"]))
        print(f"  {env_meta['id']}: {len(tasks)} tasks ({scored} with scores)")

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
