#!/usr/bin/env python3
"""Validate data.js before deploy. Runs as pre-commit hook and CI.

Checks:
1. data.js parses as valid JS/JSON
2. No null scores (every cell must be populated)
3. No empty envs (every env must have tasks)
4. Tasks sorted easy-to-hard (descending Sonnet score)
5. Model order is strongest-to-weakest
6. Every task has a non-empty description
7. Model display names are correct
"""
import json
import sys
from pathlib import Path


def load_data():
    content = Path("data.js").read_text()
    json_str = content.split("= ", 1)[1].rstrip(";\n")
    return json.loads(json_str)


def test_parses():
    """data.js must parse."""
    d = load_data()
    assert "models" in d, "missing models key"
    assert "envs" in d, "missing envs key"
    assert len(d["envs"]) > 0, "no envs"
    return d


def test_no_nulls(d):
    """Every score cell must be populated."""
    for env in d["envs"]:
        for task in env["tasks"]:
            for i, s in enumerate(task["f"]):
                assert s is not None, (
                    f"{env['name']}/{task['n']}: null score for model index {i}"
                )


def test_no_empty_envs(d):
    """Every env must have at least 1 task."""
    for env in d["envs"]:
        assert len(env["tasks"]) > 0, f"{env['name']}: no tasks"


def test_sorted_easy_to_hard(d):
    """Tasks within each env must be sorted by descending Sonnet score."""
    for env in d["envs"]:
        scores = [t["f"][0] for t in env["tasks"]]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"{env['name']}: tasks not sorted easy-to-hard "
                f"({env['tasks'][i]['n']}={scores[i]} before "
                f"{env['tasks'][i+1]['n']}={scores[i+1]})"
            )


def test_model_order(d):
    """First model must be Sonnet (strongest)."""
    assert "sonnet" in d["models"][0].lower(), (
        f"First model should be Sonnet, got {d['models'][0]}"
    )


def test_descriptions(d):
    """Every task must have a non-empty description."""
    for env in d["envs"]:
        for task in env["tasks"]:
            assert task.get("d") and len(task["d"]) > 10, (
                f"{env['name']}/{task['n']}: missing or short description"
            )


def test_model_names(d):
    """Model display names must be correct."""
    names = d.get("modelNames", {})
    assert "4.6" in names.get("claude-sonnet-4-6", ""), "Sonnet should say 4.6"


def main():
    errors = []
    try:
        d = test_parses()
    except Exception as e:
        print(f"FAIL: data.js doesn't parse: {e}")
        sys.exit(1)

    tests = [
        ("no_nulls", lambda: test_no_nulls(d)),
        ("no_empty_envs", lambda: test_no_empty_envs(d)),
        ("sorted_easy_to_hard", lambda: test_sorted_easy_to_hard(d)),
        ("model_order", lambda: test_model_order(d)),
        ("descriptions", lambda: test_descriptions(d)),
        ("model_names", lambda: test_model_names(d)),
    ]

    for name, fn in tests:
        try:
            fn()
            print(f"  PASS  {name}")
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            errors.append(name)

    if errors:
        print(f"\n{len(errors)} test(s) failed: {', '.join(errors)}")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
