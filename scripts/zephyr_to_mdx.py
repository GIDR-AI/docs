import json, os, re
from pathlib import Path

AUTO_BEGIN = "{/* AUTO:BEGIN */}"
AUTO_END = "{/* AUTO:END */}"

def slug(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s)
    return s.strip("-") or "unknown"

def clean(s: str) -> str:
    return (s or "").replace("\r\n", "\n").strip()

def pick(step: dict, *keys: str) -> str:
    for k in keys:
        v = step.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""

def render_auto(tc: dict) -> str:
    key = tc.get("key", "")
    name = clean(tc.get("name", "")) or key
    objective = clean(tc.get("objective", ""))
    precond = clean(tc.get("precondition", ""))
    steps = tc.get("steps") or []

    out = []
    out.append("## Summary")
    out.append(objective if objective else "_No objective provided in Zephyr._")
    out.append("")
    out.append("## Preconditions")
    out.append(precond if precond else "_None._")
    out.append("")
    out.append("## Steps")
    out.append("")
    out.append("| # | Action | Data | Expected |")
    out.append("|---:|---|---|---|")

    if not isinstance(steps, list) or len(steps) == 0:
        out.append("| 1 | _No steps found._ | _ | _ |")
    else:
        for i, st in enumerate(steps, start=1):
            # Handle nested structure: st['inline']['description'] etc.
            inline = st.get("inline") or {}
            # Try nested first, then top-level
            action = clean(pick(inline, "action", "description", "step", "text")) or clean(pick(st, "action", "description", "step", "text"))
            data = clean(pick(inline, "data", "testData", "input")) or clean(pick(st, "data", "testData", "input"))
            expected = clean(pick(inline, "expectedResult", "expected", "result")) or clean(pick(st, "expectedResult", "expected", "result"))
            out.append(f"| {i} | {action or '_'} | {data or '_'} | {expected or '_'} |")

    out.append("")
    out.append(f"**Zephyr key:** `{key}`")
    out.append("")
    return "\n".join(out).strip() + "\n"

def upsert_page(path: Path, frontmatter: str, auto_block: str):
    if path.exists():
        txt = path.read_text(encoding="utf-8")
        if AUTO_BEGIN in txt and AUTO_END in txt:
            # Update frontmatter if it exists
            if txt.strip().startswith("---"):
                # Find where frontmatter ends (second ---)
                lines = txt.split("\n")
                frontmatter_end = 0
                dash_count = 0
                for i, line in enumerate(lines):
                    if line.strip() == "---":
                        dash_count += 1
                        if dash_count == 2:
                            frontmatter_end = i + 1
                            break
                
                if frontmatter_end > 0:
                    # Extract manual section (between frontmatter and AUTO_BEGIN)
                    manual_section = "\n".join(lines[frontmatter_end:])
                    if AUTO_BEGIN in manual_section:
                        manual_part, auto_rest = manual_section.split(AUTO_BEGIN, 1)
                        _, post = auto_rest.split(AUTO_END, 1)
                        # Reconstruct with new frontmatter
                        new_txt = frontmatter + "\n\n" + manual_part + AUTO_BEGIN + "\n\n" + auto_block + "\n" + AUTO_END + post
                        path.write_text(new_txt, encoding="utf-8")
                        return
            
            # Fallback: just update auto section
            pre, rest = txt.split(AUTO_BEGIN, 1)
            _, post = rest.split(AUTO_END, 1)
            new_txt = pre + AUTO_BEGIN + "\n\n" + auto_block + "\n" + AUTO_END + post
            path.write_text(new_txt, encoding="utf-8")
            return

    # New file scaffold: manual section + auto block
    content = (
        frontmatter
        + "\n\n"
        + "## Notes (manual)\n\n"
        + "_Add examples, edge cases, screenshots, caveats, and cross-links here. This section is not overwritten._\n\n"
        + AUTO_BEGIN + "\n\n"
        + auto_block + "\n"
        + AUTO_END + "\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def main():
    src = Path("data/zephyr_testcases.json")
    if not src.exists():
        raise SystemExit("Missing data/zephyr_testcases.json (run Step 3 export first).")

    testcases = json.loads(src.read_text(encoding="utf-8"))
    out_dir = Path("docs/generated/testcases")

    created = 0
    updated = 0

    for tc in testcases:
        key = str(tc.get("key") or "").strip()
        if not key:
            continue

        title = clean(tc.get("name")) or key
        # Escape quotes in title for YAML frontmatter
        title_escaped = title.replace('"', '\\"')
        frontmatter = (
            "---\n"
            f'title: "{title_escaped}"\n'
            f'description: "Auto-generated from Zephyr Scale test case {key}"\n'
            "---"
        )

        auto = render_auto(tc)
        path = out_dir / f"{slug(key)}.mdx"
        existed = path.exists()
        upsert_page(path, frontmatter, auto)
        if existed:
            updated += 1
        else:
            created += 1

    print(f"Generated pages. created={created} updated={updated}")

if __name__ == "__main__":
    main()

