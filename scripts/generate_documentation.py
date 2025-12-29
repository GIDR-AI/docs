import json
import re
from pathlib import Path
from collections import defaultdict

def clean(s: str) -> str:
    return (s or "").replace("\r\n", "\n").strip()

def pick(step: dict, *keys: str) -> str:
    for k in keys:
        v = step.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def categorize_testcase(tc):
    """Improved categorization"""
    name = (tc.get("name") or "").lower()
    objective = (tc.get("objective") or "").lower()
    text = f"{name} {objective}".lower()
    
    # Authentication & Onboarding
    if any(word in text for word in ["sign in", "signin", "login", "log in", "sign-in"]):
        if "invalid" in text or "error" in text:
            return ("authentication", "signing-in", "error-cases")
        elif "forgot password" in text or "reset password" in text or "change password" in text:
            return ("authentication", "signing-in", "password-management")
        else:
            return ("authentication", "signing-in")
    elif any(word in text for word in ["sign up", "signup", "register", "registration", "sign-up"]):
        if "invalid" in text or "error" in text:
            return ("authentication", "signing-up", "error-cases")
        else:
            return ("authentication", "signing-up")
    elif "landing page" in text or ("landing" in text and "page" in text):
        return ("authentication", "landing-page")
    elif "logout" in text:
        return ("authentication", "signing-in", "logout")
    
    # Organizations and Teams
    elif any(word in text for word in ["create team", "create a team", "team creation"]):
        return ("organizations", "create-team")
    elif "member profile" in text or ("profile" in text and "member" in text):
        return ("organizations", "member-profile")
    elif "organization settings" in text or "org settings" in text:
        return ("organizations", "organization-settings")
    elif "invite member" in text or ("invite" in text and "member" in text):
        return ("organizations", "invite-members")
    
    # GIDRs (top level)
    elif "analytics" in text:
        return ("gidrs", "analytics")
    elif "mcp server" in text or ("mcp" in text and "server" in text):
        return ("gidrs", "mcp-server")
    elif "language selection" in text or ("language" in text and ("change" in text or "select" in text)):
        return ("gidrs", "language-selection")
    elif "create gidr" in text:
        return ("gidrs", "create-gidr")
    elif "members" in text and "gidr" in text:
        return ("gidrs", "members")
    
    # GIDR Info
    elif "gidr info" in text or "info popup" in text:
        return ("gidr", "info", "gidr-info")
    elif "general settings" in text or "settings drawer" in text:
        return ("gidr", "info", "general-settings")
    
    # Prompts
    elif "prompt" in text:
        return ("gidr", "prompts")
    
    # Ingestion Settings
    elif "data source" in text or "data sources" in text:
        if "file" in text:
            return ("gidr", "ingestion-settings", "data-sources", "files")
        elif "url" in text:
            return ("gidr", "ingestion-settings", "data-sources", "urls")
        elif "connector" in text:
            return ("gidr", "ingestion-settings", "data-sources", "connectors")
        elif "database" in text:
            return ("gidr", "ingestion-settings", "data-sources", "database")
        else:
            return ("gidr", "ingestion-settings", "data-sources")
    elif "file" in text and ("upload" in text or "ingest" in text or "chunk" in text):
        return ("gidr", "ingestion-settings", "data-sources", "files")
    elif "url" in text and ("add" in text or "ingest" in text):
        return ("gidr", "ingestion-settings", "data-sources", "urls")
    elif "connector" in text:
        return ("gidr", "ingestion-settings", "data-sources", "connectors")
    elif "database" in text:
        return ("gidr", "ingestion-settings", "data-sources", "database")
    elif "tag" in text:
        return ("gidr", "ingestion-settings", "tags")
    
    # Design
    elif "gidget" in text or "gidgets library" in text:
        return ("gidr", "design", "gidgets-library")
    elif "studio" in text:
        return ("gidr", "design", "studio")
    
    # Workflows
    elif "workflow" in text or "work flow" in text:
        if "node" in text:
            return ("gidr", "workflows", "nodes")
        else:
            return ("gidr", "workflows")
    elif "node" in text and ("react" in text or "flow" in text):
        return ("gidr", "workflows", "nodes")
    
    # Default
    return ("uncategorized",)

def testcase_to_doc(tc):
    """Convert a test case to documentation format"""
    key = tc.get("key", "")
    name = clean(tc.get("name", "")) or key
    objective = clean(tc.get("objective", ""))
    precond = clean(tc.get("precondition", ""))
    steps = tc.get("steps") or []
    
    doc = []
    doc.append(f"## {name}")
    doc.append("")
    if objective:
        doc.append(objective)
        doc.append("")
    
    if precond:
        doc.append("### Prerequisites")
        doc.append(precond)
        doc.append("")
    
    if steps:
        doc.append("### Steps")
        doc.append("")
        for i, st in enumerate(steps, start=1):
            inline = st.get("inline") or {}
            action = clean(pick(inline, "action", "description", "step", "text")) or clean(pick(st, "action", "description", "step", "text"))
            data = clean(pick(inline, "data", "testData", "input")) or clean(pick(st, "data", "testData", "input"))
            expected = clean(pick(inline, "expectedResult", "expected", "result")) or clean(pick(st, "expectedResult", "expected", "result"))
            
            doc.append(f"{i}. **{action or 'Action'}**")
            if data:
                doc.append(f"   - Data: `{data}`")
            if expected:
                doc.append(f"   - Expected: {expected}")
            doc.append("")
    
    doc.append(f"*Test case reference: `{key}`*")
    doc.append("")
    
    return "\n".join(doc)

def create_doc_page(category_path, testcases, base_dir):
    """Create a documentation page for a category"""
    path_parts = list(category_path)
    if path_parts[0] == "uncategorized":
        return  # Skip uncategorized for now
    
    # Map to documentation structure
    doc_map = {
        ("authentication", "signing-in"): ("authentication", "signing-in"),
        ("authentication", "signing-in", "error-cases"): ("authentication", "signing-in", "error-cases"),
        ("authentication", "signing-in", "password-management"): ("authentication", "signing-in", "password-management"),
        ("authentication", "signing-in", "logout"): ("authentication", "signing-in", "logout"),
        ("authentication", "signing-up"): ("authentication", "signing-up"),
        ("authentication", "signing-up", "error-cases"): ("authentication", "signing-up", "error-cases"),
        ("authentication", "landing-page"): ("authentication", "landing-page"),
        ("organizations", "create-team"): ("organizations", "create-team"),
        ("organizations", "member-profile"): ("organizations", "member-profile"),
        ("organizations", "organization-settings"): ("organizations", "organization-settings"),
        ("organizations", "invite-members"): ("organizations", "invite-members"),
        ("gidrs", "create-gidr"): ("gidrs", "create-gidr"),
        ("gidrs", "analytics"): ("gidrs", "analytics"),
        ("gidrs", "members"): ("gidrs", "members"),
        ("gidrs", "mcp-server"): ("gidrs", "mcp-server"),
        ("gidrs", "language-selection"): ("gidrs", "language-selection"),
        ("gidr", "info", "gidr-info"): ("gidr", "info", "gidr-info"),
        ("gidr", "info", "general-settings"): ("gidr", "info", "general-settings"),
        ("gidr", "prompts"): ("gidr", "prompts"),
        ("gidr", "ingestion-settings", "data-sources"): ("gidr", "ingestion-settings", "data-sources"),
        ("gidr", "ingestion-settings", "data-sources", "files"): ("gidr", "ingestion-settings", "data-sources", "files"),
        ("gidr", "ingestion-settings", "data-sources", "urls"): ("gidr", "ingestion-settings", "data-sources", "urls"),
        ("gidr", "ingestion-settings", "data-sources", "connectors"): ("gidr", "ingestion-settings", "data-sources", "connectors"),
        ("gidr", "ingestion-settings", "data-sources", "database"): ("gidr", "ingestion-settings", "data-sources", "database"),
        ("gidr", "ingestion-settings", "tags"): ("gidr", "ingestion-settings", "tags"),
        ("gidr", "design", "gidgets-library"): ("gidr", "design", "gidgets-library"),
        ("gidr", "design", "studio"): ("gidr", "design", "studio"),
        ("gidr", "workflows"): ("gidr", "workflows"),
        ("gidr", "workflows", "nodes"): ("gidr", "workflows", "nodes"),
    }
    
    doc_path = doc_map.get(category_path)
    if not doc_path:
        return
    
    # Create file path
    file_path = base_dir / "docs" / "manual" / "/".join(doc_path[:-1]) / f"{doc_path[-1]}.mdx"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate title from path
    title = doc_path[-1].replace("-", " ").title()
    
    AUTO_BEGIN = "{/* AUTO:BEGIN */}"
    AUTO_END = "{/* AUTO:END */}"
    
    # Generate auto content
    auto_content = []
    if testcases:
        auto_content.append("## Test Cases")
        auto_content.append("")
        auto_content.append("The following test cases cover this functionality:")
        auto_content.append("")
        for tc in testcases:
            auto_content.append(testcase_to_doc(tc))
    else:
        auto_content.append("## TODO")
        auto_content.append("")
        auto_content.append("_No test cases found for this section. Add documentation here._")
        auto_content.append("")
    
    auto_block = "\n".join(auto_content).strip() + "\n"
    
    # Check if file exists and preserve manual content
    if file_path.exists():
        txt = file_path.read_text(encoding="utf-8")
        if AUTO_BEGIN in txt and AUTO_END in txt:
            # Preserve content before and after AUTO markers
            pre, rest = txt.split(AUTO_BEGIN, 1)
            _, post = rest.split(AUTO_END, 1)
            new_txt = pre + AUTO_BEGIN + "\n\n" + auto_block + AUTO_END + post
            file_path.write_text(new_txt, encoding="utf-8")
            return file_path
    
    # New file - create full structure
    content = []
    content.append("---")
    content.append(f'title: "{title}"')
    content.append(f'description: "Documentation for {title}"')
    content.append("---")
    content.append("")
    content.append(f"# {title}")
    content.append("")
    content.append(AUTO_BEGIN)
    content.append("")
    content.append(auto_block)
    content.append(AUTO_END)
    content.append("")
    content.append("## Notes (manual)")
    content.append("")
    content.append("_Add examples, edge cases, screenshots, caveats, and cross-links here. This section is not overwritten._")
    content.append("")
    
    file_path.write_text("\n".join(content), encoding="utf-8")
    return file_path

def main():
    src = Path("data/zephyr_testcases.json")
    testcases = json.loads(src.read_text(encoding="utf-8"))
    base_dir = Path(".")
    
    categorized = defaultdict(list)
    
    for tc in testcases:
        category = categorize_testcase(tc)
        categorized[category].append(tc)
    
    # Create documentation pages
    created = []
    for category, tcs in sorted(categorized.items()):
        path = create_doc_page(category, tcs, base_dir)
        if path:
            created.append(path)
            print(f"Created: {path.relative_to(base_dir)} ({len(tcs)} test cases)")
    
    print(f"\nCreated {len(created)} documentation pages")
    
    # Save mapping for reference
    mapping = {}
    for category, tcs in categorized.items():
        mapping[' > '.join(category)] = [tc['key'] for tc in tcs]
    
    output = Path("data/testcase_categories.json")
    output.write_text(json.dumps(mapping, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()

