{
  "findings_file": "autoresearch/cc-switch-notes/21-ch7-source-support-findings.md",
  "total_claims_checked": 15,
  "verdicts": {
    "ok": 11,
    "wrong": 4,
    "hallucination": 0,
    "stale": 0,
    "unsupported": 0,
    "ambiguous": 0
  },
  "high_severity": 0,
  "medium_severity": 1,
  "low_severity": 3,
  "medium_issues": [
    "claude_desktop_config.rs size says 14.0KB in roadmap text (line 5229), actual is 61.5KB"
  ],
  "low_issues": [
    "lib.rs:38 is not the duplicate pub use; line 40 is",
    "9 preset files, not 8",
    "cleanup range end is 1599, not 1598"
  ],
  "additional_verified": [
    "Provider.settings_config is indeed serde_json::Value (provider.rs:14) confirming the strong-typing recommendation",
    "79 match blocks on app_type exist, confirming the 10+ duplicate match claim",
    "Naming inconsistency confirmed: mix of get_, read_, fetch_ prefixes across services",
    "Error messages are genuinely mixed Chinese/English"
  ]
}