#!/usr/bin/env bash
set -euo pipefail

# Autoresearch benchmark: measures study notes completeness and depth
# Primary metric: completeness (0-100 composite score)
# Secondary: chapters, words, code_refs, sections, examples, slop_patterns

cd "$(dirname "$0")"

python3 docs/verify_notes.py

exit 0
