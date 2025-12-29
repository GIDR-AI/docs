import json
from pathlib import Path
from collections import defaultdict

def categorize_testcase(tc):
    """Categorize a test case based on its name, objective, and content"""
    key = tc.get("key", "")
    name = (tc.get("name") or "").lower()
    objective = (tc.get("objective") or "").lower()
    text = f"{name} {objective}".lower()
    
    categories = []
    
    # Authentication & Onboarding
    if any(word in text for word in ["sign in", "signin", "login", "log in", "sign-in"]):
        if "invalid" in text or "error" in text:
            categories.append(("authentication", "signing-in", "error-cases"))
        else:
            categories.append(("authentication", "signing-in"))
    elif any(word in text for word in ["sign up", "signup", "register", "registration", "sign-up"]):
        if "invalid" in text or "error" in text:
            categories.append(("authentication", "signing-up", "error-cases"))
        else:
            categories.append(("authentication", "signing-up"))
    elif "landing page" in text or "landing" in text:
        categories.append(("authentication", "landing-page"))
    elif "forgot password" in text or "reset password" in text or "change password" in text:
        categories.append(("authentication", "signing-in", "password-management"))
    
    # Organizations and Teams
    elif any(word in text for word in ["create team", "create a team", "team creation"]):
        categories.append(("organizations", "create-team"))
    elif "member profile" in text or "profile" in text:
        categories.append(("organizations", "member-profile"))
    elif "organization settings" in text or "org settings" in text:
        categories.append(("organizations", "organization-settings"))
    elif "invite member" in text or "invite" in text:
        categories.append(("organizations", "invite-members"))
    
    # GIDRs (top level)
    elif "analytics" in text:
        categories.append(("gidrs", "analytics"))
    elif "mcp server" in text or "mcp" in text:
        categories.append(("gidrs", "mcp-server"))
    elif "language selection" in text or "language" in text:
        categories.append(("gidrs", "language-selection"))
    elif "create gidr" in text and "team" in text:
        categories.append(("gidrs", "create-gidr"))
    
    # GIDR Info
    elif "gidr info" in text or "info popup" in text:
        categories.append(("gidr", "info", "gidr-info"))
    
    # Prompts
    elif "prompt" in text:
        categories.append(("gidr", "prompts"))
    
    # Ingestion Settings
    elif "data source" in text or "data sources" in text:
        categories.append(("gidr", "ingestion-settings", "data-sources"))
    elif "file" in text and ("upload" in text or "ingest" in text):
        categories.append(("gidr", "ingestion-settings", "data-sources", "files"))
    elif "url" in text and ("add" in text or "ingest" in text):
        categories.append(("gidr", "ingestion-settings", "data-sources", "urls"))
    elif "connector" in text:
        categories.append(("gidr", "ingestion-settings", "data-sources", "connectors"))
    elif "database" in text:
        categories.append(("gidr", "ingestion-settings", "data-sources", "database"))
    elif "tag" in text:
        categories.append(("gidr", "ingestion-settings", "tags"))
    
    # Design
    elif "gidget" in text or "gidgets library" in text:
        categories.append(("gidr", "design", "gidgets-library"))
    elif "studio" in text:
        categories.append(("gidr", "design", "studio"))
    
    # Workflows
    elif "workflow" in text or "work flow" in text:
        categories.append(("gidr", "workflows"))
    elif "node" in text and ("workflow" in text or "flow" in text):
        categories.append(("gidr", "workflows", "nodes"))
    
    # Default fallback
    if not categories:
        categories.append(("uncategorized",))
    
    return categories[0] if categories else ("uncategorized",)

def main():
    src = Path("data/zephyr_testcases.json")
    testcases = json.loads(src.read_text(encoding="utf-8"))
    
    categorized = defaultdict(list)
    
    for tc in testcases:
        category = categorize_testcase(tc)
        categorized[category].append(tc)
    
    # Print summary
    print("Test Case Categorization Summary:\n")
    for category, tcs in sorted(categorized.items()):
        print(f"{' > '.join(category)}: {len(tcs)} test cases")
        for tc in tcs[:3]:  # Show first 3
            print(f"  - {tc['key']}: {tc['name']}")
        if len(tcs) > 3:
            print(f"  ... and {len(tcs) - 3} more")
        print()
    
    # Save mapping
    mapping = {}
    for category, tcs in categorized.items():
        mapping[' > '.join(category)] = [tc['key'] for tc in tcs]
    
    output = Path("data/testcase_categories.json")
    output.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    print(f"\nSaved categorization to {output}")
    
    return categorized

if __name__ == "__main__":
    main()

