{
  "findings_file": "autoresearch/cc-switch-notes/04-ch1-line-ref-findings.md",
  "total_findings": 20,
  "issues_found": 12,
  "ok_findings": 8,
  "summary": {
    "wrong": 4,
    "stale": 7,
    "ambiguous": 1,
    "ok": 8
  },
  "severity_breakdown": {
    "high": 0,
    "medium": 7,
    "low": 5
  },
  "key_issues": [
    "Command count inconsistency: diagram says ~266, text says ~271, actual is 267 (Finding 1)",
    "Module counts all wrong: commands/ 34→31, services/ 25→26, proxy/ 35+→31 (Findings 2-4)",
    "Frontend line counts significantly stale: useProxyStatus.ts 185→245, useDirectorySettings.ts 275→373 (Findings 8-9)",
    "All lib/query/ file line counts off by exactly 1 line (Finding 12)",
    "Session usage sync loop reference points to line 999 instead of correct 972 (Finding 6)"
  ],
  "positive_findings": "All 39 lib.rs:line references in the startup diagram are correct. All exit flow references are correct. Plugin count (9), module count (34), and lib.rs line count (1825) are all verified. All struct/type references in store.rs, database/mod.rs, settings.rs, switch_lock.rs, services/proxy.rs, app_config.rs are correct."
}