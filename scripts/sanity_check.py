#!/usr/bin/env python3
import json
import sys

# Try to load .env if available (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except (ImportError, PermissionError):
    pass  # Not required for this script

try:
    with open("data/zephyr_testcases.json", "r", encoding="utf-8") as f:
        d = json.load(f)
    print("testcases:", len(d))
    print("first keys:", [x.get("key") for x in d[:5]])
except FileNotFoundError:
    print("Error: data/zephyr_testcases.json not found")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in data/zephyr_testcases.json: {e}")
    sys.exit(1)

