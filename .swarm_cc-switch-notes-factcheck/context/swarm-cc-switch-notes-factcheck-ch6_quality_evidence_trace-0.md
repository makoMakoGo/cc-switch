{
  "findings_file": "autoresearch/cc-switch-notes/19-ch6-quality-evidence-findings.md",
  "total_findings": 28,
  "verdict_summary": {
    "hallucination": 1,
    "wrong": 4,
    "stale_minor": 4,
    "ambiguous": 2,
    "ok_with_nuance": 5,
    "ok": 12
  },
  "critical_findings": [
    {
      "finding": 8,
      "severity": "high",
      "verdict": "hallucination",
      "issue": "`tool_config_xxx` vs `xxx_config` naming claim is fabricated — grep returns 0 matches for `tool_config` as a naming pattern in cc-switch code. Only occurrence is a local variable in transform_gemini.rs mapping to a Gemini API field.",
      "note_location": "§6.3 命名和组织问题"
    },
    {
      "finding": 5,
      "severity": "medium",
      "verdict": "wrong",
      "issue": "§7.2 refactoring table says `claude_desktop_config.rs（14.0KB）` but actual size is 61.4KB (62939 bytes). Off by ~47KB.",
      "note_location": "§7.2 中等重构"
    },
    {
      "finding": 6,
      "severity": "medium",
      "verdict": "wrong",
      "issue": "4 of 5 hook line counts wrong: useSettings 512→505, useProxyStatus 185→245, useDirectorySettings 275→373, useDragSort 95→119.",
      "note_location": "§1.3 状态管理"
    },
    {
      "finding": 9,
      "severity": "medium",
      "verdict": "wrong",
      "issue": "proxy_request_logs claimed 15 columns, actually 25 columns (schema.rs:184-196).",
      "note_location": "§6.3 数据库层 AI Slop"
    }
  ]
}