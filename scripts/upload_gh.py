#!/usr/bin/env python3
"""
GitHub API uploader using gh CLI - uploads all committed files to GitHub repo
"""
import os
import subprocess
import json

REPO = "Benjamindaoson/reliability-annotation"

def gh_exec(args):
    result = subprocess.run(
        ["gh", "api", "--method", args[0] if isinstance(args[0], str) else "GET",
         "--field", f"message=Add {args[-1]}" if args[0] == "PUT" else "message=Get contents"] +
         [f"--field={k}={v}" for k, v in args[1] if isinstance(args[1], dict)],
        capture_output=True, text=True, cwd="/d/01_work/Reliability-Bottleneck-Shift"
    )
    return result

# Get all files from HEAD commit
result = subprocess.run(
    ["git", "ls-tree", "-r", "--name-only", "HEAD"],
    capture_output=True, text=True, cwd="/d/01_work/Reliability-Bottleneck-Shift"
)
files = result.stdout.strip().split("\n")
print(f"Found {len(files)} files to upload")
