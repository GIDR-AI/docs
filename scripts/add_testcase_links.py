import re
from pathlib import Path

def add_testcase_links(content):
    """Add hyperlinks to test case references"""
    
    # First, check if content already has links to avoid double-processing
    if '/docs/generated/testcases/' in content:
        # Remove existing nested links first
        content = re.sub(
            r'\[\[`(CP-T\d+)`\]\(/docs/generated/testcases/\1\)\]\(/docs/generated/testcases/\1\)',
            r'[`\1`](/docs/generated/testcases/\1)',
            content
        )
    
    # Pattern 1: *Test case reference: `CP-T123`* (not already linked)
    def replace_reference(match):
        tc_key = match.group(1)
        # Check if already linked
        if f'[{tc_key}]' in content[max(0, match.start()-20):match.end()+20]:
            return match.group(0)
        return f'*Test case reference: [`{tc_key}`](/docs/generated/testcases/{tc_key})*'
    
    content = re.sub(
        r'\*Test case reference: `(CP-T\d+)`\*',
        replace_reference,
        content
    )
    
    # Pattern 2: - **CP-T123**: Description (not already linked)
    def replace_list_item(match):
        tc_key = match.group(1)
        description = match.group(2)
        # Check if already linked
        if f'[{tc_key}]' in match.group(0):
            return match.group(0)
        return f'- **[`{tc_key}`](/docs/generated/testcases/{tc_key})**: {description}'
    
    content = re.sub(
        r'^- \*\*(CP-T\d+)\*\*: (.+)$',
        replace_list_item,
        content,
        flags=re.MULTILINE
    )
    
    return content

def process_file(file_path):
    """Process a single file"""
    try:
        content = file_path.read_text(encoding="utf-8")
        new_content = add_testcase_links(content)
        
        if content != new_content:
            file_path.write_text(new_content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    docs_dir = Path("docs/manual")
    updated_count = 0
    
    # Process all MDX files in manual directory
    for mdx_file in docs_dir.rglob("*.mdx"):
        if process_file(mdx_file):
            updated_count += 1
            print(f"Updated: {mdx_file.relative_to(Path('.'))}")
    
    print(f"\nAdded hyperlinks to test case references in {updated_count} files")

if __name__ == "__main__":
    main()

