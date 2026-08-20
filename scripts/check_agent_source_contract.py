#!/usr/bin/env python3
"""Portable CI contract check for the PhantomNet agent source tree.

This script verifies source and packaging inputs only. It does not claim that a native
binary has been produced or that the agent has run on Linux, Windows, or Android.
"""

from __future__ import annotations

import compileall
import json
from pathlib import Path
import sys
from typing import Any


REQUIRED_PATHS = (
    "phantomnet_agent/main.py",
    "phantomnet_agent/requirements.txt",
    "phantomnet_agent/pyinstaller/agent-linux.spec",
    "phantomnet_agent/pyinstaller/agent-windows.spec",
)


def validate(repository_root: Path) -> dict[str, Any]:
    missing = [path for path in REQUIRED_PATHS if not (repository_root / path).is_file()]
    compiled = compileall.compile_dir(
        repository_root / "phantomnet_agent",
        quiet=1,
        force=True,
        workers=1,
    )
    python_source_count = sum(1 for _ in (repository_root / "phantomnet_agent").rglob("*.py"))
    return {
        "contract": "agent_source_contract_v1",
        "required_path_count": len(REQUIRED_PATHS),
        "missing_paths": missing,
        "python_source_count": python_source_count,
        "python_compilation_passed": compiled,
        "native_binary_proof": False,
        "device_runtime_proof": False,
    }


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    result = validate(repository_root)
    artifacts = repository_root / "artifacts"
    artifacts.mkdir(exist_ok=True)
    output = artifacts / "agent_source_contract.json"
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not result["missing_paths"] and result["python_compilation_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
