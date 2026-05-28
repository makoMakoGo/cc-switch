#!/usr/bin/env python3
"""Verify study notes completeness and emit METRIC lines for autoresearch."""
import re
import sys
import os

NOTES_PATH = os.path.join(os.path.dirname(__file__), "cc-switch-source-notes.md")

CHAPTER_RE = re.compile(r"^##\s+第\s*(\d+)\s*章", re.MULTILINE)
CODE_REF_RE = re.compile(r"`[^`]*\.(rs|ts|tsx):\d+")
SECTION_RE = re.compile(r"^###\s+\d+\.\d+", re.MULTILINE)
CONCRETE_EXAMPLE_RE = re.compile(r"```(rust|typescript|tsx|json|text)")
WORD_RE = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z]+")
AI_SLOP_RE = re.compile(r"(AI\s*[Ss]lop|屎山|过度抽象|膨胀|wrapper|冗余|重复|臃肿)", re.IGNORECASE)

def main():
    if not os.path.exists(NOTES_PATH):
        print(f"ERROR: Notes file not found at {NOTES_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(NOTES_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Chapter count
    chapters = CHAPTER_RE.findall(content)
    chapter_count = len(chapters)

    # Word count: use wc -w for honest count
    import subprocess
    result = subprocess.run(['wc', '-w', NOTES_PATH], capture_output=True, text=True)
    word_count = int(result.stdout.strip().split()[0])

    # Code references (file:line style)
    code_refs = CODE_REF_RE.findall(content)
    code_ref_count = len(code_refs)

    # Sections
    sections = SECTION_RE.findall(content)
    section_count = len(sections)

    # Concrete code examples
    examples = CONCRETE_EXAMPLE_RE.findall(content)
    example_count = len(examples)

    # AI Slop pattern mentions
    slop_mentions = AI_SLOP_RE.findall(content)
    slop_count = len(slop_mentions)

    # Primary metric: completeness score (0-100)
    # 40 pts for chapters (7 max), 30 pts for word depth (target 15000), 30 pts for code refs (target 80)
    chapter_score = min(chapter_count / 7.0, 1.0) * 40
    word_score = min(word_count / 15000.0, 1.0) * 30
    ref_score = min(code_ref_count / 80.0, 1.0) * 30
    completeness = chapter_score + word_score + ref_score

    print(f"METRIC completeness={completeness:.1f}")
    print(f"METRIC chapters={chapter_count}")
    print(f"METRIC words={word_count}")
    print(f"METRIC code_refs={code_ref_count}")
    print(f"METRIC sections={section_count}")
    print(f"METRIC examples={example_count}")
    print(f"METRIC slop_patterns={slop_count}")

    sys.exit(0)

if __name__ == "__main__":
    main()
