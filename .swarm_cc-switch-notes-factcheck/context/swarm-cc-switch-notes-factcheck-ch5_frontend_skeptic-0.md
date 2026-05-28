{
  "findings_count": 11,
  "high": 2,
  "medium": 4,
  "low": 5,
  "output_file": "autoresearch/cc-switch-notes/18-ch5-skeptic-findings.md",
  "highlights": [
    "providersApi signatures are entirely fabricated (wrong method names, param order, return types) — verdict: hallucination",
    "claude_desktop_config.rs size in §7.2 says 14KB but actual is 61.5KB — verdict: wrong",
    "UseSettingsResult, UseImportExportResult, hermesKeys, hermesApi all have missing members — verdict: wrong",
    "useProxyStatus polling interval contradicts itself between Ch1 (5s) and Ch5 (2s); actual is 2s — verdict: stale"
  ]
}