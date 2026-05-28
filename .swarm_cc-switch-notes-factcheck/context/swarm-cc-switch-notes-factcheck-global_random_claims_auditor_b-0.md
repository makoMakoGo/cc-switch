{
  "findings_file": "autoresearch/cc-switch-notes/26-random-claims-b-findings.md",
  "summary": {
    "total_findings": 10,
    "by_severity": {
      "high": 1,
      "medium": 4,
      "low": 5
    },
    "by_verdict": {
      "wrong": 4,
      "stale": 5,
      "ambiguous": 1
    },
    "verified_ok": 34
  },
  "key_findings": [
    "Finding 1 (high): DAO file size contradictions — table at §3.3 is correct but bullet points below it use sizes from wrong directories (proxy.rs 7.5KB vs actual 33.9KB, settings.rs 28.9KB vs actual 11.9KB, etc.)",
    "Finding 2 (medium): commands/mod.rs submodule count — notes claim 33, actual is 31",
    "Finding 3 (medium): Tauri command count — notes claim ~271, actual #[tauri::command] count is 249",
    "Finding 4 (medium): useProxyStatus polling interval — §1.3 says 5s, actual code is 2s, §5.2 correctly says 2s",
    "Finding 7 (medium): Hook line counts in §1.3 — 4 of 5 hooks have wrong values (useSettings 512→505, useProxyStatus 185→245, useDirectorySettings 275→373, useDragSort 95→119)"
  ]
}