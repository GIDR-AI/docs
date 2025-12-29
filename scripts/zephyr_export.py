import os, json, time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE = os.getenv("ZEPHYR_BASE_URL", "https://api.zephyrscale.smartbear.com/v2")
TOKEN = os.environ["ZEPHYR_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

def get(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def list_testcases():
    start_at, max_results = 0, 100
    all_items = []
    while True:
        data = get(f"{BASE}/testcases", params={"startAt": start_at, "maxResults": max_results})
        items = data.get("values") or data.get("items") or []
        if not items:
            break
        all_items.extend(items)
        # Check if this is the last page
        if data.get("isLast", False):
            break
        start_at += len(items)
        time.sleep(0.1)
    return all_items

def get_steps(testcase_key: str):
    # Endpoint: /testcases/{key}/teststeps
    try:
        return get(f"{BASE}/testcases/{testcase_key}/teststeps")
    except Exception as e:
        print(f"    Warning: Failed to fetch steps for {testcase_key}: {e}")
        return None

def fetch_steps_batch(testcase_keys, batch_size=10):
    """Fetch test steps for multiple test cases concurrently"""
    results = {}
    
    def fetch_one(key):
        return key, get_steps(key)
    
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Submit all tasks
        future_to_key = {executor.submit(fetch_one, key): key for key in testcase_keys}
        
        # Collect results as they complete
        for future in as_completed(future_to_key):
            key, steps_payload = future.result()
            if steps_payload:
                steps = steps_payload.get("values") or steps_payload.get("items") or steps_payload
                if not isinstance(steps, list):
                    steps = []
            else:
                steps = []
            results[key] = steps
            # Small delay to avoid overwhelming the API
            time.sleep(0.05)
    
    return results

def main():
    print("Fetching test cases...")
    tcs = list_testcases()
    print(f"Found {len(tcs)} test cases. Fetching steps in batches...")
    
    # Extract test case keys
    testcase_data = {}
    keys_to_fetch = []
    for tc in tcs:
        key = tc.get("key")
        if not key:
            continue
        keys_to_fetch.append(key)
        testcase_data[key] = {
            "name": tc.get("name") or "",
            "objective": tc.get("objective") or tc.get("description") or "",
            "precondition": tc.get("precondition") or "",
            "labels": tc.get("labels") or [],
            "components": tc.get("components") or [],
        }
    
    # Fetch steps in batches
    batch_size = 10
    all_steps = {}
    total_batches = (len(keys_to_fetch) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(keys_to_fetch))
        batch_keys = keys_to_fetch[start_idx:end_idx]
        
        print(f"  Fetching steps for batch {batch_num + 1}/{total_batches} ({len(batch_keys)} test cases)...")
        batch_steps = fetch_steps_batch(batch_keys, batch_size=batch_size)
        all_steps.update(batch_steps)
        
        # Delay between batches to be respectful to the API
        if batch_num < total_batches - 1:
            time.sleep(0.2)
    
    # Combine test case data with steps
    out = []
    for key in keys_to_fetch:
        out.append({
            "key": key,
            "name": testcase_data[key]["name"],
            "objective": testcase_data[key]["objective"],
            "precondition": testcase_data[key]["precondition"],
            "labels": testcase_data[key]["labels"],
            "components": testcase_data[key]["components"],
            "steps": all_steps.get(key, [])
        })

    os.makedirs("data", exist_ok=True)
    with open("data/zephyr_testcases.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"✓ Exported {len(out)} test cases to data/zephyr_testcases.json")

if __name__ == "__main__":
    main()

