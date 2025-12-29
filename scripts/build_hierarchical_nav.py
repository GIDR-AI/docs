import json
from pathlib import Path
from collections import defaultdict

def build_hierarchical_navigation(pages):
    """Build hierarchical navigation structure from page paths"""
    
    # Organize pages by their path structure
    structure = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    root_pages = []
    
    for page in pages:
        if not page.startswith("docs/manual/"):
            continue
        
        # Remove docs/manual/ prefix
        rel_path = page.replace("docs/manual/", "")
        parts = rel_path.split("/")
        
        if len(parts) == 1:
            # Top level page (e.g., index, documentation-structure)
            root_pages.append(page)
        elif len(parts) == 2:
            # Second level (e.g., authentication/signing-in)
            section = parts[0]
            if "_pages" not in structure[section]:
                structure[section]["_pages"] = []
            structure[section]["_pages"].append(page)
        elif len(parts) == 3:
            # Third level (e.g., authentication/signing-in/error-cases)
            section = parts[0]
            subsection = parts[1]
            if "_pages" not in structure[section][subsection]:
                structure[section][subsection]["_pages"] = []
            structure[section][subsection]["_pages"].append(page)
        elif len(parts) == 4:
            # Fourth level (e.g., gidr/ingestion-settings/data-sources/files)
            section = parts[0]
            subsection = parts[1]
            subsubsection = parts[2]
            structure[section][subsection][subsubsection].append(page)
    
    structure["_root"] = root_pages
    return structure

def format_title(path_part):
    """Convert path part to readable title"""
    return path_part.replace("-", " ").title()

def build_nav_groups(structure):
    """Build Mintlify navigation groups from structure"""
    groups = []
    
    # Root pages first
    if "_root" in structure:
        for page in sorted(structure["_root"]):
            groups.append(page)
    
    # Then organized sections
    for section in sorted(structure.keys()):
        if section == "_root":
            continue
        
        section_pages = structure[section]
        
        # Check if this section has direct pages or subsections
        has_direct_pages = "_pages" in section_pages and section_pages["_pages"]
        has_subsections = any(k != "_pages" for k in section_pages.keys())
        
        if has_subsections:
            # Create a group for this section
            section_group = {
                "group": format_title(section),
                "pages": []
            }
            
            # Add direct pages first
            if has_direct_pages:
                section_group["pages"].extend(sorted(section_pages["_pages"]))
            
            # Add subsections
            for subsection in sorted(section_pages.keys()):
                if subsection == "_pages":
                    continue
                
                subsection_data = section_pages[subsection]
                
                # Check if subsection has direct pages or sub-subsections
                has_sub_pages = "_pages" in subsection_data and subsection_data["_pages"]
                has_subsubsections = any(k != "_pages" for k in subsection_data.keys())
                
                if has_subsubsections:
                    # Create nested group
                    subsection_group = {
                        "group": format_title(subsection),
                        "pages": []
                    }
                    
                    # Add direct pages
                    if has_sub_pages:
                        subsection_group["pages"].extend(sorted(subsection_data["_pages"]))
                    
                    # Add sub-subsections as pages
                    for subsubsection in sorted(subsection_data.keys()):
                        if subsubsection == "_pages":
                            continue
                        subsection_group["pages"].extend(sorted(subsection_data[subsubsection]))
                    
                    section_group["pages"].append(subsection_group)
                elif has_sub_pages:
                    # Subsection with only pages - add as nested group
                    subsection_group = {
                        "group": format_title(subsection),
                        "pages": sorted(subsection_data["_pages"])
                    }
                    section_group["pages"].append(subsection_group)
            
            groups.append(section_group)
        elif has_direct_pages:
            # Section with only direct pages - add as simple group
            groups.append({
                "group": format_title(section),
                "pages": sorted(section_pages["_pages"])
            })
    
    return groups

def main():
    base_dir = Path(".")
    docs_json_path = base_dir / "docs.json"
    
    # Read existing docs.json
    with open(docs_json_path, "r") as f:
        docs = json.load(f)
    
    # Get all manual pages
    manual_pages = []
    manual_dir = Path("docs/manual")
    for mdx_file in manual_dir.rglob("*.mdx"):
        rel_path = mdx_file.relative_to(Path("docs"))
        page_path = str(rel_path)[:-4]  # Remove .mdx
        if not page_path.startswith("docs/"):
            page_path = f"docs/{page_path}"
        manual_pages.append(page_path)
    
    # Build hierarchical structure
    structure = build_hierarchical_navigation(sorted(manual_pages))
    
    # Build navigation groups
    nav_groups = build_nav_groups(structure)
    
    # Update docs.json
    groups = docs.get("navigation", {}).get("groups", [])
    
    # Find Manual group and replace it
    found = False
    for i, group in enumerate(groups):
        if group.get("group") == "Manual":
            # Replace with hierarchical structure
            groups[i] = {
                "group": "Manual",
                "pages": nav_groups
            }
            found = True
            break
    
    if not found:
        # Manual group not found, add it
        groups.append({
            "group": "Manual",
            "pages": nav_groups
        })
    
    docs["navigation"]["groups"] = groups
    
    # Write back
    with open(docs_json_path, "w") as f:
        json.dump(docs, f, indent=2)
        f.write("\n")
    
    # Verify write
    with open(docs_json_path, "r") as f:
        verify_docs = json.load(f)
        for group in verify_docs.get("navigation", {}).get("groups", []):
            if group.get("group") == "Manual":
                if group["pages"] and isinstance(group["pages"][0], dict):
                    print("✅ Successfully wrote hierarchical structure")
                else:
                    print("❌ Structure not written correctly")
                break
    
    print(f"Built hierarchical navigation with {len(nav_groups)} top-level items")
    print("\nNavigation structure:")
    for item in nav_groups[:5]:
        if isinstance(item, dict):
            print(f"  - {item['group']}: {len(item.get('pages', []))} items")
        else:
            print(f"  - {item}")

if __name__ == "__main__":
    main()

