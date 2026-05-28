{
  "findings_file": "autoresearch/cc-switch-notes/25-random-claims-a-findings.md",
  "total_findings": 10,
  "by_verdict": {
    "wrong": 8,
    "ambiguous": 1,
    "ok_sample": 18
  },
  "by_severity": {
    "medium": 7,
    "low": 3
  },
  "key_pattern": "DAO summary text (lines 649-659) has 5 wrong file sizes while the preceding table is correct — the summary was written separately and never cross-checked against the table or actual file sizes. Same pattern in commands summary (line 735) and refactoring chapter (line 5229).",
  "verified_ok_sample": [
    "main.rs 22 lines",
    "lib.rs 1825 lines / 34 modules",
    "271 invoke_handler commands",
    "setup closure 284-1070",
    "AppState store.rs:6",
    "Database database/mod.rs:76 Mutex<Connection>",
    "SETTINGS_STORE settings.rs:519",
    "mutate_settings settings.rs:574 private, param mutator",
    "ProxyConfig default port 15721",
    "9 plugins",
    "SCHEMA_VERSION=10",
    "ProxyService services/proxy.rs:55",
    "SwitchLockManager switch_lock.rs:14",
    "forwarder.rs 3100 lines/122KB",
    "App.tsx 1604 lines",
    "hooks/ 25 files/3642 lines",
    "is_additive_mode() app_config.rs:373"
  ]
}