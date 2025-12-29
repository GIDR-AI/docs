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

def classify_test_type(tc):
    """Classify test case as happy path, negative, edge, etc."""
    name = (tc.get("name") or "").lower()
    objective = (tc.get("objective") or "").lower()
    text = f"{name} {objective}".lower()
    
    if any(word in text for word in ["invalid", "error", "fail", "wrong", "incorrect", "negative"]):
        return "negative"
    elif any(word in text for word in ["edge", "boundary", "limit", "extreme"]):
        return "edge"
    elif any(word in text for word in ["performance", "perf", "load", "stress"]):
        return "performance"
    elif any(word in text for word in ["security", "auth", "permission", "access"]):
        return "security"
    else:
        return "happy"

def extract_prerequisites(testcases):
    """Extract common prerequisites from test cases"""
    preconditions = set()
    for tc in testcases:
        precond = clean(tc.get("precondition", ""))
        if precond:
            preconditions.add(precond)
    return sorted(list(preconditions))

def normalize_step_action(action: str) -> str:
    """Normalize step actions to consistent verbs"""
    action = clean(action)
    if not action:
        return "Perform action"
    
    # Common patterns
    if "click" in action.lower():
        return action.replace("click", "Click").replace("Click on", "Click")
    if "enter" in action.lower() or "type" in action.lower():
        return action.replace("enter", "Enter").replace("type", "Enter")
    if "verify" in action.lower() or "validate" in action.lower():
        return action.replace("verify", "Verify").replace("validate", "Verify")
    if "open" in action.lower():
        return action.replace("open", "Open")
    if "navigate" in action.lower():
        return action.replace("navigate", "Navigate")
    
    # Capitalize first letter
    return action[0].upper() + action[1:] if action else action

def format_step_as_procedure(step, step_num):
    """Format a step as a readable procedure instead of table row"""
    inline = step.get("inline") or {}
    action = clean(pick(inline, "action", "description", "step", "text")) or clean(pick(step, "action", "description", "step", "text"))
    data = clean(pick(inline, "data", "testData", "input")) or clean(pick(step, "data", "testData", "input"))
    expected = clean(pick(inline, "expectedResult", "expected", "result")) or clean(pick(step, "expectedResult", "expected", "result"))
    
    action = normalize_step_action(action)
    
    lines = []
    lines.append(f"**Step {step_num}: {action}**")
    lines.append("")
    
    if data:
        lines.append(f"**Input:** `{data}`")
        lines.append("")
    
    if expected:
        lines.append(f"**Result:** {expected}")
        lines.append("")
    
    return "\n".join(lines)

def clean_html(text: str) -> str:
    """Remove HTML tags from text"""
    if not text:
        return ""
    # Simple HTML tag removal
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&amp;', '&', text)
    return clean(text)

def generate_happy_path_procedure(happy_tests):
    """Generate clean happy path procedure using Mintlify Steps component"""
    if not happy_tests:
        return None
    
    # Use the first happy path test as the canonical procedure
    primary_test = happy_tests[0]
    steps = primary_test.get("steps") or []
    
    if not steps:
        return None
    
    lines = []
    lines.append("<Steps>")
    lines.append("")
    
    for i, step in enumerate(steps, start=1):
        inline = step.get("inline") or {}
        action = clean(pick(inline, "action", "description", "step", "text")) or clean(pick(step, "action", "description", "step", "text"))
        data = clean_html(pick(inline, "data", "testData", "input")) or clean_html(pick(step, "data", "testData", "input"))
        expected = clean(pick(inline, "expectedResult", "expected", "result")) or clean(pick(step, "expectedResult", "expected", "result"))
        
        action = normalize_step_action(action)
        
        # Extract a short title from action (first 50 chars)
        title = action[:50] + "..." if len(action) > 50 else action
        title = title.replace('"', "'")  # Avoid quote issues
        
        lines.append(f'<Step title="{title}">')
        lines.append("")
        lines.append(action)
        lines.append("")
        
        if data and data not in ["_", ""]:
            lines.append(f"**Input:** `{data}`")
            lines.append("")
        
        if expected:
            lines.append(f"**Expected result:** {expected}")
            lines.append("")
        
        lines.append("</Step>")
        lines.append("")
    
    lines.append("</Steps>")
    
    return "\n".join(lines)

def generate_errors_section(negative_tests):
    """Generate errors and troubleshooting from negative tests using Mintlify components"""
    if not negative_tests:
        return None
    
    lines = []
    lines.append("## Errors and Troubleshooting")
    lines.append("")
    lines.append("The following errors may occur and how to resolve them:")
    lines.append("")
    
    for tc in negative_tests:
        name = clean(tc.get("name", ""))
        objective = clean(tc.get("objective", ""))
        steps = tc.get("steps") or []
        
        if steps:
            # Extract error condition and expected result
            last_step = steps[-1] if steps else {}
            inline = last_step.get("inline") or {}
            error_msg = clean(pick(inline, "expectedResult", "expected", "result")) or clean(pick(last_step, "expectedResult", "expected", "result"))
            
            lines.append(f"### {name}")
            lines.append("")
            
            if objective:
                lines.append(objective)
                lines.append("")
            
            if error_msg:
                lines.append("<Warning>")
                lines.append(f"**Error:** {error_msg}")
                lines.append("</Warning>")
                lines.append("")
            
            # Extract what causes the error (from steps)
            if len(steps) > 1:
                error_cause_step = steps[-2] if len(steps) > 1 else steps[0]
                cause_inline = error_cause_step.get("inline") or {}
                cause_action = clean(pick(cause_inline, "description", "action")) or clean(pick(error_cause_step, "description", "action"))
                if cause_action:
                    lines.append(f"**Cause:** {cause_action}")
                    lines.append("")
            
            lines.append(f"*Test case reference: `{tc.get('key')}`*")
            lines.append("")
    
    return "\n".join(lines)

def generate_topic_page(topic_name, topic_path, testcases, base_dir):
    """Generate a feature-level documentation page"""
    # Classify test cases
    happy_tests = [tc for tc in testcases if classify_test_type(tc) == "happy"]
    negative_tests = [tc for tc in testcases if classify_test_type(tc) == "negative"]
    edge_tests = [tc for tc in testcases if classify_test_type(tc) == "edge"]
    
    # Get primary happy path test for overview
    primary_test = happy_tests[0] if happy_tests else testcases[0] if testcases else None
    
    if not primary_test:
        return None
    
    # Create file path
    file_path = base_dir / "docs" / "manual" / "/".join(topic_path[:-1]) / f"{topic_path[-1]}.mdx"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate title
    title = topic_path[-1].replace("-", " ").title()
    
    AUTO_BEGIN = "{/* AUTO:BEGIN */}"
    AUTO_END = "{/* AUTO:END */}"
    
    # Build content
    content = []
    content.append("---")
    content.append(f'title: "{title}"')
    content.append(f'description: "How to use {title} - procedures, examples, and troubleshooting"')
    content.append("---")
    content.append("")
    content.append(f"# {title}")
    content.append("")
    content.append(AUTO_BEGIN)
    content.append("")
    
    # Overview (from objective)
    if primary_test:
        objective = clean(primary_test.get("objective", ""))
        if objective:
            content.append("## Overview")
            content.append("")
            content.append(objective)
            content.append("")
            content.append("<Info>")
            content.append("This feature allows you to accomplish the task described above. Follow the procedures below to get started.")
            content.append("</Info>")
            content.append("")
    
    # Prerequisites
    prerequisites = extract_prerequisites(testcases)
    if prerequisites:
        content.append("## Prerequisites")
        content.append("")
        for precond in prerequisites:
            content.append(f"- {precond}")
        content.append("")
    
    # Happy Path Procedure
    if happy_tests:
        content.append("## Procedure")
        content.append("")
        procedure = generate_happy_path_procedure(happy_tests)
        if procedure:
            content.append(procedure)
        else:
            content.append("_Procedure steps will be added here._")
        content.append("")
    
    # Parameters/Fields (extracted from test data, cleaned)
    if happy_tests:
        all_data = set()
        for tc in happy_tests:
            for step in tc.get("steps", []):
                inline = step.get("inline") or {}
                data = clean_html(pick(inline, "data", "testData", "input")) or clean_html(pick(step, "data", "testData", "input"))
                if data and data not in ["_", ""] and len(data) < 200:  # Filter out very long/complex data
                    all_data.add(data)
        
        if all_data and len(all_data) <= 10:  # Only show if reasonable number
            content.append("## Parameters")
            content.append("")
            content.append("The following parameters are used in this process:")
            content.append("")
            for data in sorted(all_data):
                content.append(f"- `{data}`")
            content.append("")
    
    # Errors and Troubleshooting
    if negative_tests or edge_tests:
        errors_section = generate_errors_section(negative_tests + edge_tests)
        if errors_section:
            content.append(errors_section)
    
    # Examples (placeholder for manual content)
    content.append("## Examples")
    content.append("")
    content.append("<Note>")
    content.append("Add practical examples here with realistic data and expected outcomes.")
    content.append("</Note>")
    content.append("")
    
    # Traceability
    content.append("## Related Test Cases")
    content.append("")
    content.append("This documentation is derived from the following test cases:")
    content.append("")
    for tc in sorted(testcases, key=lambda x: x.get("key", "")):
        key = tc.get("key", "")
        name = clean(tc.get("name", ""))
        test_type = classify_test_type(tc)
        content.append(f"- **{key}**: {name} ({test_type})")
    content.append("")
    
    content.append(AUTO_END)
    content.append("")
    content.append("## Notes (manual)")
    content.append("")
    content.append("_Add examples, edge cases, screenshots, caveats, and cross-links here. This section is not overwritten._")
    content.append("")
    
    # Check if file exists and preserve manual content
    if file_path.exists():
        txt = file_path.read_text(encoding="utf-8")
        if AUTO_BEGIN in txt and AUTO_END in txt:
            pre, rest = txt.split(AUTO_BEGIN, 1)
            _, post = rest.split(AUTO_END, 1)
            new_txt = pre + AUTO_BEGIN + "\n\n" + "\n".join(content[content.index(AUTO_BEGIN)+1:content.index(AUTO_END)]) + "\n" + AUTO_END + post
            file_path.write_text(new_txt, encoding="utf-8")
            return file_path
    
    # New file
    file_path.write_text("\n".join(content), encoding="utf-8")
    return file_path

def categorize_testcase(tc):
    """Categorize test case to topic (same as before)"""
    name = (tc.get("name") or "").lower()
    objective = (tc.get("objective") or "").lower()
    text = f"{name} {objective}".lower()
    
    # Authentication & Onboarding
    if any(word in text for word in ["sign in", "signin", "login", "log in", "sign-in"]):
        if "invalid" in text or "error" in text:
            return ("authentication", "signing-in", "error-cases")
        elif "forgot password" in text or "reset password" in text or "change password" in text:
            return ("authentication", "signing-in", "password-management")
        elif "logout" in text:
            return ("authentication", "signing-in", "logout")
        else:
            return ("authentication", "signing-in")
    elif any(word in text for word in ["sign up", "signup", "register", "registration", "sign-up"]):
        if "invalid" in text or "error" in text:
            return ("authentication", "signing-up", "error-cases")
        else:
            return ("authentication", "signing-up")
    elif "landing page" in text or ("landing" in text and "page" in text):
        return ("authentication", "landing-page")
    
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
    
    return ("uncategorized",)

def main():
    src = Path("data/zephyr_testcases.json")
    testcases = json.loads(src.read_text(encoding="utf-8"))
    base_dir = Path(".")
    
    # Group test cases by topic
    topics = defaultdict(list)
    for tc in testcases:
        category = categorize_testcase(tc)
        if category[0] != "uncategorized":
            topics[category].append(tc)
    
    # Generate feature-level pages
    created = []
    for topic_path, tcs in sorted(topics.items()):
        path = generate_topic_page(
            topic_path[-1],
            topic_path,
            tcs,
            base_dir
        )
        if path:
            created.append(path)
            print(f"Created: {path.relative_to(base_dir)} ({len(tcs)} test cases)")
    
    print(f"\nGenerated {len(created)} feature-level documentation pages")

if __name__ == "__main__":
    main()

