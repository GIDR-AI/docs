import json
from pathlib import Path

def get_all_mdx_files(base_dir):
    """Get all MDX files in the manual directory"""
    manual_dir = Path(base_dir) / "docs" / "manual"
    mdx_files = []
    
    for mdx_file in manual_dir.rglob("*.mdx"):
        # Get relative path from docs/
        rel_path = mdx_file.relative_to(Path(base_dir) / "docs")
        # Remove .mdx extension and ensure it starts with docs/
        page_path = str(rel_path)[:-4]
        if not page_path.startswith("docs/"):
            page_path = f"docs/{page_path}"
        mdx_files.append(page_path)
    
    return sorted(mdx_files)

def build_navigation_structure(pages):
    """Build navigation structure from pages"""
    structure = {
        "authentication": [],
        "organizations": [],
        "gidrs": [],
        "gidr": {
            "info": [],
            "prompts": [],
            "ingestion-settings": {
                "data-sources": []
            },
            "design": [],
            "workflows": []
        }
    }
    
    for page in pages:
        parts = page.split("/")
        if len(parts) >= 3 and parts[1] == "manual":
            section = parts[2]
            if section == "authentication":
                structure["authentication"].append(page)
            elif section == "organizations":
                structure["organizations"].append(page)
            elif section == "gidrs":
                structure["gidrs"].append(page)
            elif section == "gidr":
                if len(parts) >= 4:
                    subsection = parts[3]
                    if subsection == "info":
                        structure["gidr"]["info"].append(page)
                    elif subsection == "prompts":
                        structure["gidr"]["prompts"].append(page)
                    elif subsection == "ingestion-settings":
                        if len(parts) >= 5 and parts[4] == "data-sources":
                            structure["gidr"]["ingestion-settings"]["data-sources"].append(page)
                        else:
                            structure["gidr"]["ingestion-settings"]["data-sources"].append(page)
                    elif subsection == "design":
                        structure["gidr"]["design"].append(page)
                    elif subsection == "workflows":
                        structure["gidr"]["workflows"].append(page)
    
    return structure

def main():
    base_dir = Path(".")
    docs_json_path = base_dir / "docs.json"
    
    # Read existing docs.json
    with open(docs_json_path, "r") as f:
        docs = json.load(f)
    
    # Get all manual pages
    manual_pages = get_all_mdx_files(base_dir)
    
    # Build navigation groups
    groups = docs.get("navigation", {}).get("groups", [])
    
    # Find or create Manual group
    manual_group = None
    for group in groups:
        if group.get("group") == "Manual":
            manual_group = group
            break
    
    if not manual_group:
        manual_group = {"group": "Manual", "pages": []}
        groups.append(manual_group)
    
    # Update Manual group pages - ensure all start with docs/
    all_pages = ["docs/manual/index", "docs/manual/documentation-structure"]
    for page in manual_pages:
        if not page.startswith("docs/"):
            all_pages.append(f"docs/{page}")
        else:
            all_pages.append(page)
    manual_group["pages"] = sorted(set(all_pages))  # Remove duplicates and sort
    
    # Update docs.json
    docs["navigation"]["groups"] = groups
    
    # Write back
    with open(docs_json_path, "w") as f:
        json.dump(docs, f, indent=2)
        f.write("\n")
    
    print(f"Updated docs.json with {len(manual_pages)} manual documentation pages")
    print(f"Total pages in Manual group: {len(manual_group['pages'])}")

if __name__ == "__main__":
    main()

