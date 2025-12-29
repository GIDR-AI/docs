from pathlib import Path

# Sections that need placeholder pages
missing_sections = [
    ("authentication", "landing-page"),
    ("authentication", "signing-in", "password-management"),
    ("organizations", "create-team"),
    ("gidrs", "analytics"),
    ("gidrs", "members"),
    ("gidr", "ingestion-settings", "data-sources", "urls"),
    ("gidr", "ingestion-settings", "tags"),
    ("gidr", "workflows"),
]

base_dir = Path(".")

for section_path in missing_sections:
    file_path = base_dir / "docs" / "manual" / "/".join(section_path[:-1]) / f"{section_path[-1]}.mdx"
    
    # Skip if already exists
    if file_path.exists():
        continue
    
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    title = section_path[-1].replace("-", " ").title()
    
    content = f"""---
title: "{title}"
description: "Documentation for {title}"
---

# {title}

{{/* AUTO:BEGIN */}}

## TODO

_No test cases found for this section. Add documentation here._

{{/* AUTO:END */}}

## Notes (manual)

_Add examples, edge cases, screenshots, caveats, and cross-links here. This section is not overwritten._
"""
    
    file_path.write_text(content, encoding="utf-8")
    print(f"Created placeholder: {file_path.relative_to(base_dir)}")

