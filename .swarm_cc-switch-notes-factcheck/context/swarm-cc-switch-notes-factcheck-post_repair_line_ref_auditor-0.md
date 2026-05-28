{
  "verdict": "FAIL",
  "must_fix_count": 7,
  "must_fix_issues": [
    {
      "id": "1.1",
      "location": "docs/cc-switch-source-notes.md:2876",
      "description": "Stray code fence marker creates unclosed fence; depth never returns to 0 after line 2875",
      "fix": "Delete line 2876"
    },
    {
      "id": "1.2",
      "location": "docs/cc-switch-source-notes.md:253-254",
      "description": "Old '34 个子模块' line not removed when corrected '31 个子模块' was added; breaks ASCII chart",
      "fix": "Delete line 253"
    },
    {
      "id": "1.3",
      "location": "docs/cc-switch-source-notes.md:206-207",
      "description": "Old '每 5 秒' line not removed when corrected '每 2 秒' was added; breaks diagram",
      "fix": "Delete line 206"
    },
    {
      "id": "1.4",
      "location": "docs/cc-switch-source-notes.md:203,232",
      "description": "localStorage key 'currentView' should be 'cc-switch-last-view'",
      "fix": "Replace at both locations"
    },
    {
      "id": "1.5",
      "location": "docs/cc-switch-source-notes.md:756",
      "description": "Stale '34 个模块声明'; source has 35 mod declarations in lib.rs:1-36",
      "fix": "Change to '35 个模块声明'"
    },
    {
      "id": "1.6",
      "location": "docs/cc-switch-source-notes.md:759",
      "description": "Stale '约 271 个 Tauri 命令'; source has exactly 266 commands",
      "fix": "Change to '~266 个 Tauri 命令'"
    },
    {
      "id": "1.7",
      "location": "docs/cc-switch-source-notes.md:246",
      "description": "Stale '声明 34 个模块'; source has 35 mod declarations",
      "fix": "Change to '声明 35 个模块'"
    }
  ],
  "duplicate_block_issues": 12,
  "false_alarms_rejected": 52,
  "report_path": "autoresearch/cc-switch-notes/31-post-repair-line-ref-auditor.md"
}