{
  "findings_written": "autoresearch/cc-switch-notes/08-ch3-core-skeptic-findings.md",
  "scope": "§3.1–§3.5 only",
  "total_findings": 10,
  "by_verdict": {
    "wrong": 3,
    "ambiguous": 1,
    "stale": 1,
    "ok": 5
  },
  "critical_findings": [
    {
      "id": 3,
      "section": "§3.5",
      "severity": "high",
      "issue": "DAO bullet list has fabricated file sizes for 5 of 12 files, directly contradicting the correct table above it in the same section. proxy.rs listed as 7.5KB (actual 33.9KB), settings.rs as 28.9KB (actual 11.9KB), mcp.rs as 19.6KB (actual 4.1KB)."
    },
    {
      "id": 1,
      "section": "§3.2",
      "severity": "medium",
      "issue": "AppError variant line numbers systematically off by 1 for 11 of 16 variants (notes count attribute line, not variant definition)."
    },
    {
      "id": 2,
      "section": "§3.4",
      "severity": "medium",
      "issue": "UsageScript struct shows 6 fields but actual struct has 13 — missing access_token, user_id, template_type, auto_query_interval, coding_plan_provider (NewAPI and Coding Plan features)."
    }
  ],
  "verified_ok": [
    "§3.1 config.rs function line numbers (all 10 correct)",
    "§3.3 AppType enum variants, methods, switch/additive classification",
    "§3.3 McpApps/SkillApps/MultiAppConfig/McpServer/McpRoot/InstalledSkill",
    "§3.4 Provider struct (all 12 fields), ProviderManager, methods",
    "§3.5 SETTINGS_STORE, mutate_settings, SwitchLockManager, ProxyService, HotSwitchOutcome"
  ]
}