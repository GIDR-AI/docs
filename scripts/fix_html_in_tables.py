import re
from pathlib import Path
from html import unescape

def clean_html_in_table_cells(content):
    """Remove HTML tags from table cells and convert to plain text"""
    
    def clean_cell(match):
        cell_content = match.group(0)
        # Remove HTML tags but keep the text
        # Remove <strong>, </strong>, <br>, <br/>, and attributes like id="isPasted"
        cleaned = re.sub(r'<strong[^>]*>', '', cell_content)
        cleaned = re.sub(r'</strong>', '', cleaned)
        cleaned = re.sub(r'<br\s*/?>', ' ', cleaned)  # Replace <br> with space
        cleaned = re.sub(r'&nbsp;', ' ', cleaned)  # Replace &nbsp; with space
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Collapse multiple spaces
        cleaned = cleaned.strip()
        return cleaned
    
    # Pattern to match table cells (content between | and |)
    # This is tricky because we need to handle pipes inside cells
    lines = content.split('\n')
    result = []
    
    for line in lines:
        if '|' in line and line.strip().startswith('|'):
            # It's a table row
            # Check if it's a separator row (contains --- or :---)
            if re.search(r'[-:]+', line):
                # It's a separator row, keep it as is but clean HTML
                cleaned = re.sub(r'<strong[^>]*>', '', line)
                cleaned = re.sub(r'</strong>', '', cleaned)
                cleaned = re.sub(r'<br\s*/?>', ' ', cleaned)
                cleaned = re.sub(r'&nbsp;', ' ', cleaned)
                result.append(cleaned)
            else:
                # It's a data row
                # Split by | but preserve spacing
                parts = line.split('|')
                cleaned_parts = []
                for i, part in enumerate(parts):
                    # Remove HTML tags from each cell
                    cleaned = re.sub(r'<strong[^>]*>', '', part)
                    cleaned = re.sub(r'</strong>', '', cleaned)
                    cleaned = re.sub(r'<br\s*/?>', ' ', cleaned)
                    cleaned = re.sub(r'&nbsp;', ' ', cleaned)
                    cleaned = re.sub(r'\s+', ' ', cleaned)
                    cleaned = cleaned.strip()
                    # Add space around content for proper markdown table formatting
                    if cleaned:
                        cleaned = f' {cleaned} '
                    cleaned_parts.append(cleaned)
                result.append('|'.join(cleaned_parts))
        else:
            result.append(line)
    
    return '\n'.join(result)

def process_file(file_path):
    """Process a single file"""
    try:
        content = file_path.read_text(encoding="utf-8")
        new_content = clean_html_in_table_cells(content)
        
        if content != new_content:
            file_path.write_text(new_content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    testcases_dir = Path("docs/generated/testcases")
    updated_count = 0
    
    # Process all MDX files
    for mdx_file in testcases_dir.glob("*.mdx"):
        if process_file(mdx_file):
            updated_count += 1
            print(f"Updated: {mdx_file.name}")
    
    print(f"\nFixed HTML in {updated_count} test case files")

if __name__ == "__main__":
    main()

