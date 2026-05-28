{
  "report": "autoresearch/cc-switch-notes/30-post-repair-frontend-audit.md",
  "verdict": "FAIL",
  "unresolved_must_fix": 4,
  "suggested_edits": 2,
  "false_alarms_rejected": 5,
  "claims_verified_correct": 31,
  "issues": [
    {
      "id": "U1",
      "location": "§1.3 lines 206-207",
      "description": "Duplicate useProxyStatus() entry — old '每 5 秒' line not removed after repair added corrected '运行时每 2 秒' line"
    },
    {
      "id": "U2",
      "location": "§1.4 line 246",
      "description": "lib.rs module count says 34, actual is 35 (fixed in §6 but not §1)"
    },
    {
      "id": "U3",
      "location": "§1.4 lines 253-254",
      "description": "Duplicate commands/ submodule count — old '34 个子模块' line not removed after repair added '31 个子模块'"
    },
    {
      "id": "U4",
      "location": "§6.4 line 5232",
      "description": "'9 个 preset 文件（237KB）— 结构几乎一样' — mcpPresets.ts is structurally different from provider presets, and 237KB only covers the 8 provider presets"
    }
  ]
}