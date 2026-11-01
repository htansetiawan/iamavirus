#!/usr/bin/env python3
"""Build and run correctness checks, recording source hashes and raw results."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
report = {"scope": "Correctness only; no strength claim", "checks": [],
          "sources": {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for folder in ("src", "tests") for p in sorted((HERE/folder).glob("*"))}}
common = ["gcc", "-std=c11", "-pthread", "-D_POSIX_C_SOURCE=199309L", "-Ibuild/src"]
other = ["build/src/"+name+".c" for name in ("board", "belief", "movemodel", "eval", "search", "front", "sfeval")]
jobs = [
    ("entry_rewards", ["tests/test_entry_rewards.c", "src/cfr.c"]),
    ("root_integration", ["tests/test_root_integration.c", "src/cfr.c", *other]),
    ("kuhn", ["tests/test_kuhn.c", "src/cfr.c"]),
]
env = {k:v for k,v in os.environ.items() if not k.startswith(("MIST_", "FOW_"))}
for sanitizer in (False, True):
    for name, sources in jobs:
        if sanitizer and name == "kuhn":
            continue
        output = "build/test_"+name+("_san" if sanitizer else "")
        flags = ["-O1", "-g", "-fno-omit-frame-pointer", "-fsanitize=address,undefined"] if sanitizer else ["-O2"]
        command = [*common, *flags, *sources, "-lm", "-o", output]
        compiled = subprocess.run(command, capture_output=True, text=True, env=env)
        entry = {"name": name, "sanitized": sanitizer, "compile_command": command,
                 "compile_exit": compiled.returncode, "compile_output": compiled.stdout+compiled.stderr}
        if compiled.returncode == 0:
            result = subprocess.run(["taskset", "-c", "0,1", output], capture_output=True, text=True, env=env)
            entry.update(exit=result.returncode, output=result.stdout+result.stderr,
                         binary_sha256=hashlib.sha256(Path(output).read_bytes()).hexdigest())
        report["checks"].append(entry)
        (HERE/"correctness.json").write_text(json.dumps(report, indent=2)+"\n")
        print(name, "sanitized" if sanitizer else "optimized", entry.get("exit", "compile failed"), flush=True)
        if entry.get("exit", 1) != 0:
            raise SystemExit(1)
