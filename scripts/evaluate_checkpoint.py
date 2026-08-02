#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from checkpoint_contract import load_expectations, validate


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a checkpoint against a benchmark contract")
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("expectations", type=Path)
    args = parser.parse_args()
    profile, terms = load_expectations(args.expectations)
    result = validate(args.checkpoint.read_text(encoding="utf-8"), profile, terms)
    print(result.to_json())
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
