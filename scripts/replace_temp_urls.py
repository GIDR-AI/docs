import re
from pathlib import Path

def replace_urls_in_file(file_path):
    """Replace temporary GIDR URLs with app.gidr.ai"""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content
        
        # Pattern to match URLs like https://gidr-*.web.app/...
        pattern = r'https://gidr-[^/]+\.web\.app(/[^\s`"]*)'
        
        def replace_url(match):
            path = match.group(1)  # Get the path part
            return f'https://app.gidr.ai{path}'
        
        content = re.sub(pattern, replace_url, content)
        
        if content != original:
            file_path.write_text(content, encoding="utf-8")
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    docs_dir = Path("docs")
    replaced_count = 0
    
    # Find all MDX files
    for mdx_file in docs_dir.rglob("*.mdx"):
        if replace_urls_in_file(mdx_file):
            replaced_count += 1
            print(f"Updated: {mdx_file.relative_to(Path('.'))}")
    
    print(f"\nReplaced URLs in {replaced_count} files")

if __name__ == "__main__":
    main()

