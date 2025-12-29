#!/usr/bin/env python3
"""Quick connectivity test for Zephyr Scale API"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

token = os.getenv("ZEPHYR_TOKEN")
base_url = os.getenv("ZEPHYR_BASE_URL", "https://api.zephyrscale.smartbear.com/v2")

if not token:
    print("Error: ZEPHYR_TOKEN environment variable is not set")
    print("Please set it in .env file or as an environment variable")
    exit(1)

print("Testing connectivity to Zephyr Scale API...")
print(f"Base URL: {base_url}")
print("")

try:
    r = requests.get(
        f"{base_url}/testcases?page=1&size=1",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        timeout=10
    )
    r.raise_for_status()
    # Show first 800 characters (redacting token)
    output = r.text[:800]
    print(output)
except Exception as e:
    print(f"Error: {e}")
    exit(1)

