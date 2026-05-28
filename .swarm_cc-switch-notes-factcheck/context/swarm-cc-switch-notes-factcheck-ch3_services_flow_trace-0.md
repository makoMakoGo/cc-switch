{
  "file": "autoresearch/cc-switch-notes/11-ch3-services-findings.md",
  "total_findings": 17,
  "by_verdict": {
    "hallucination": 3,
    "wrong": 10,
    "ambiguous": 2,
    "stale": 2
  },
  "by_severity": {
    "high": 3,
    "medium": 10,
    "low": 4
  },
  "critical_issues": [
    "3 hallucinated 'common pattern' functions in section 3.6 (build_live_config, switch_provider, import_from_live) that don't exist in any config module",
    "5 database file sizes wrong (mod.rs, schema.rs, migration.rs, and 2 DAO line counts off by 5-6x)",
    "5 DAO inline text sizes contradict the table directly above them",
    "proxy_config table missing 4 columns (enable_logging, streaming_idle_timeout, created_at, updated_at)"
  ]
}