{
  "findings_file": "autoresearch/cc-switch-notes/12-ch3-db-services-skeptic-findings.md",
  "total_findings": 20,
  "non_ok_findings": 13,
  "ok_findings": 7,
  "by_verdict": {
    "wrong": 13,
    "hallucination": 0,
    "stale": 0,
    "unsupported": 0,
    "ambiguous": 0
  },
  "by_severity": {
    "high": 5,
    "medium": 8,
    "low": 7
  },
  "key_issues": [
    "3 config paths wrong (Codex .toml not .json, OpenCode wrong dir, OpenClaw wrong filename)",
    "Common patterns claim unsupported - switch_provider/import_from_live don't exist in config modules",
    "proxy_config SQL missing 4 columns (enable_logging, streaming_idle_timeout, timestamps)",
    "proxy_request_logs SQL missing 2 cost columns",
    "session_log_sync SQL missing last_synced_at column",
    "Database module sizes: 3 of 4 wrong (up to 6.7× off)",
    "DAO line counts: 6 of 12 wrong (up to 6.1× off)",
    "Services file sizes: 11 of 22 wrong (30-37× off, likely ls -la column capture error)",
    "commands submodule count: 33 claimed vs 31 actual",
    "DAO prose sizes contradict DAO table (5 wrong)",
    "Database::init() pseudocode omits key steps and shows wrong error handling"
  ]
}