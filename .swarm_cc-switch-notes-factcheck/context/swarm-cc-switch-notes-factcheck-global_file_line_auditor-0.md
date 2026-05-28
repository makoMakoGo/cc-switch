{
  "findings_file": "autoresearch/cc-switch-notes/23-global-file-line-findings.md",
  "total_findings": 18,
  "by_severity": {
    "high": 3,
    "medium": 4,
    "low": 11
  },
  "high_severity_summary": [
    "Finding 1: .run() line number wrong — notes say lib.rs:1379, actual is lib.rs:1383",
    "Finding 3: Query layer file sizes hallucinated — 6 of 9 files have wrong sizes (e.g. omo.ts claimed 12.1KB, actual 2.6KB)",
    "Finding 4: DAO bullet-point sizes contradict the table directly above them — 5 files with wrong sizes"
  ],
  "medium_severity_summary": [
    "Finding 2: commands/mod.rs submodule count wrong — notes say 33, actual is 31",
    "Finding 5: app_store::refresh() function name wrong — should be refresh_app_config_dir_override()",
    "Finding 6: Frontend hook line counts stale — useProxyStatus.ts off by 60, useDirectorySettings.ts off by 98",
    "Finding 7: commands/provider.rs size bullet confused with src/provider.rs"
  ],
  "verified_ok_spot_check": "120+ specific file.rs:NNN references verified correct across all chapters"
}