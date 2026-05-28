# Chapter 4 Adversarial Findings — Fault Tolerance / Circuit Breaker / Streaming / Error

Agent: proxy-fault-skeptic
Date: 2026-05-28

---

## F1 — Duplicate `### 4.3` heading

**Location**: Ch4, lines 3877 and 3964

**Claim (first)**: `### 4.3 ProxyState 和 ProxyServer`
**Claim (second)**: `### 4.3 认证和路由`

**Verdict**: wrong

**Source evidence**: Both headings use `### 4.3`. The second should be `### 4.4` (and subsequent headings renumbered). This breaks document navigation and any automated TOC extraction.

**Severity**: medium

**Replacement**: Change the second `### 4.3 认证和路由` to `### 4.4 认证和路由`, and shift `### 4.4 故障转移和熔断` → `### 4.5`, `### 4.5 代理接管` → `### 4.6`.

---

## F2 — Duplicate `ClientFormat` enum block

**Location**: Ch4, lines 3749–3758 (first) and 3945–3954 (second)

**Claim**: The `ClientFormat` enum with its 6 variants and `from_path()`/`from_body()` descriptions appears twice, nearly verbatim.

**Verdict**: wrong

**Source evidence**: `src-tauri/src/proxy/session.rs:19-32` defines the enum once. The notes duplicate the entire block. The second occurrence (inside the "4.3 认证和路由" section) adds no new information.

**Severity**: medium

**Replacement**: Remove the second `ClientFormat` block (lines 3945–3957) entirely. The first occurrence at lines 3749–3761 is sufficient and correctly placed in the session module section.

---

## F3 — Duplicate `session` module description

**Location**: Ch4, lines 3762–3767 (first) and 3958–3963 (second)

**Claim**: Session module description (Session ID extraction for Claude/Codex/other) appears twice.

**Verdict**: wrong

**Source evidence**: `src-tauri/src/proxy/session.rs:1-10` contains the module-level doc comment once. The notes duplicate the description.

**Severity**: low

**Replacement**: Remove lines 3958–3963 (the second occurrence). Keep only lines 3762–3767.

---

## F4 — Error classification misrepresented as simple ≥500/<500 split

**Location**: Ch4, §4.1.2, lines 3831–3833

**Claim**:
> **错误分类**（`forwarder.rs:223`）：
> - Provider 错误（`Timeout`、`ForwardFailed`、`UpstreamError >= 500`）→ 继续故障转移
> - 客户端错误（`UpstreamError < 500`）→ 直接返回，没有 provider 能修复

**Verdict**: wrong

**Source evidence**: The code at `forwarder.rs:223` is inside `handle_rectifier_retry_failure()` — a helper that handles **only** rectifier retry failures, not the main forwarding loop. The main error classification used in the forwarding loop is `categorize_proxy_error()` at `forwarder.rs:1888-1920`, which has significantly different semantics:

| Error | `categorize_proxy_error` result |
|-------|-------------------------------|
| `Timeout`, `ForwardFailed`, `ProviderUnhealthy` | Retryable |
| `UpstreamError` 401, 403, 404, 408, 409, 429, 451 | **Retryable** (not NonRetryable) |
| `UpstreamError` 400, 405, 406, 413, 414, 415, 422 | NonRetryable |
| `UpstreamError` 501 | **NonRetryable** (unlike other 5xx) |
| `UpstreamError` all other 5xx (500, 502–504, 520+) | Retryable |
| `AuthError`, `ConfigError`, `TransformError`, `StreamIdleTimeout` | Retryable |
| `NoAvailableProvider` | NonRetryable |
| Everything else | NonRetryable |

The notes' "≥ 500 = provider error, < 500 = client error" is a misleading oversimplification. Many 4xx codes (401, 403, 429) are **Retryable** because a different provider may hold different credentials or quota. And 501 is **NonRetryable** because the upstream protocol genuinely doesn't support it.

**Severity**: high

**Replacement**:
```
**错误分类**（`forwarder.rs:1888`，`categorize_proxy_error()`）：

主转发循环使用 `ErrorCategory` 三态分类：
- **Retryable** → 记录到熔断器，继续故障转移到下一家 provider
- **NonRetryable** → 释放 HalfOpen permit（不污染熔断器），直接返回客户端
- **ClientAbort** → 同 NonRetryable（客户端断连）

分类规则（非简单的 ≥500/<500）：
- `Timeout`、`ForwardFailed`、`ProviderUnhealthy` → Retryable
- `UpstreamError` 按状态码细分：
  - 400/405/406/413/414/415/422/501 → NonRetryable（请求体或协议本身有问题）
  - 401/403/404/408/409/429/451 + 所有 5xx（除 501）→ Retryable（换 provider 可能成功）
- `AuthError`、`ConfigError`、`TransformError`、`StreamIdleTimeout` → Retryable
- `NoAvailableProvider`、`DatabaseError`、`Internal` 等 → NonRetryable
```

---

## F5 — `session.rs` line count off by 1

**Location**: Ch4, line 3762

**Claim**: `session.rs，627 行`

**Verdict**: stale

**Source evidence**: `wc -l src-tauri/src/proxy/session.rs` → 626 lines.

**Severity**: low

**Replacement**: `session.rs，626 行`

---

## F6 — `sse.rs` line count off by 1

**Location**: Ch4, line 3938

**Claim**: `sse.rs，346 行`

**Verdict**: stale

**Source evidence**: `wc -l src-tauri/src/proxy/sse.rs` → 345 lines.

**Severity**: low

**Replacement**: `sse.rs，345 行`

---

## F7 — `provider_router.rs` line count inconsistent (523 vs 524)

**Location**: Ch4, line 3670 says "523 行", line 3966 says "524 行"

**Claim**: Two different line counts for the same file.

**Verdict**: stale

**Source evidence**: `wc -l src-tauri/src/proxy/provider_router.rs` → 523 lines. The first mention (523) is correct; the second (524) is off by 1.

**Severity**: low

**Replacement**: Line 3966: `provider_router.rs，523 行` → `provider_router.rs，523 行` (already correct at line 3670; fix line 3966 from 524 to 523).

---

## F8 — `ProxyError` struct listing is truncated/mangled

**Location**: Ch4, lines 3878–3892

**Claim**: Notes show `ProxyError` enum starting at `proxy/error.rs:10` with variants listed, but the block is abruptly cut off after `ProviderUnhealthy(String)` at line 3891, then jumps to `**proxy/ 目录统计**` at line 3892 without closing the code block or listing the remaining 10 variants.

**Verdict**: wrong

**Source evidence**: `src-tauri/src/proxy/error.rs:10-77` defines all 20 variants. The notes only show the first 10 (AlreadyRunning through ProviderUnhealthy) and silently omit the remaining 10: `UpstreamError`, `MaxRetriesExceeded`, `DatabaseError`, `ConfigError`, `TransformError`, `InvalidRequest`, `Timeout`, `StreamIdleTimeout`, `AuthError`, `Internal`. The code block is also missing its closing ` ``` `.

**Severity**: medium

**Replacement**: Complete the enum listing with all 20 variants and close the code block:
```rust
#[derive(Debug, Error)]
pub enum ProxyError {           // proxy/error.rs:10
    AlreadyRunning,             // 服务器已在运行
    NotRunning,                 // 服务器未运行
    BindFailed(String),         // 地址绑定失败
    StopTimeout,                // 停止超时
    StopFailed(String),         // 停止失败
    ForwardFailed(String),      // 请求转发失败
    NoAvailableProvider,        // 无可用的Provider
    AllProvidersCircuitOpen,    // 所有供应商已熔断
    NoProvidersConfigured,      // 未配置供应商
    ProviderUnhealthy(String),  // Provider不健康
    UpstreamError { status: u16, body: Option<String> },  // 上游 HTTP 错误
    MaxRetriesExceeded,         // 超过最大重试次数
    DatabaseError(String),      // 数据库错误
    ConfigError(String),        // 配置错误
    TransformError(String),     // 格式转换错误
    InvalidRequest(String),     // 无效请求
    Timeout(String),            // 超时
    StreamIdleTimeout(u64),     // 流式响应空闲超时
    AuthError(String),          // 认证失败
    Internal(String),           // 内部错误
}
```

---

## F9 — `ProxyServer` stop flow omits timeout detail

**Location**: Ch4, §4.1.3, lines 3849–3852

**Claim**:
> **停止流程**（`stop()`）：
> 1. 发送关闭信号（`shutdown_tx.send(())`）
> 2. 等待服务器任务完成（`server_handle.await`）
> 3. 更新状态（`running = false`）

**Verdict**: ambiguous

**Source evidence**: `src-tauri/src/proxy/server.rs:221-251` shows:
1. `shutdown_tx.send(())` — correct
2. `tokio::time::timeout(Duration::from_secs(5), handle).await` — the notes omit the 5-second timeout and the three-outcome match (Ok(Ok), Ok(Err), Err timeout)
3. `running = false` happens inside the spawned task at line 207, not in `stop()` itself. The `stop()` method returns `Ok(())` or `Err(ProxyError::StopTimeout)` / `Err(ProxyError::StopFailed)`.

The notes' third step implies `stop()` directly sets `running = false`, but it's actually set by the server task upon receiving the shutdown signal. The 5-second timeout is an important operational detail (prevents indefinite hang on stop).

**Severity**: medium

**Replacement**:
```
**停止流程**（`stop()`，`server.rs:221`）：
1. 发送关闭信号（`shutdown_tx.send(())`），无 channel 则返回 `NotRunning`
2. 带 5 秒超时等待服务器任务结束（`tokio::time::timeout(5s, handle)`）
   - 成功 → `Ok(())`
   - 任务 panic → `Err(StopFailed)`
   - 超时 → `Err(StopTimeout)`
3. 状态 `running = false` 由服务器任务退出时自动设置（`server.rs:207`）
```

---

## F10 — `ErrorCategory` enum and `categorize_error()` function exist but are `#[allow(dead_code)]`

**Location**: Not mentioned in notes (gap)

**Claim**: Notes do not mention `ErrorCategory` or `categorize_error()` at all.

**Verdict**: ambiguous

**Source evidence**: `src-tauri/src/proxy/error.rs:178-206` defines `ErrorCategory { Retryable, NonRetryable, ClientAbort }` and `categorize_error(&reqwest::Error)`. Both are marked `#[allow(dead_code)]`. However, `ErrorCategory` IS actively used — by `categorize_proxy_error()` on `RequestForwarder` (forwarder.rs:1888), which is the actual error classification used in the forwarding loop. The notes' omission of this three-state classification system means a reader cannot understand the failover decision logic.

**Severity**: medium

**Replacement**: Add to §4.4 or §4.1.2:
```
**ErrorCategory 枚举**（`proxy/error.rs:179`）：
```rust
pub enum ErrorCategory {
    Retryable,    // 网络问题、5xx、可切换 provider 解决
    NonRetryable, // 4xx 特定状态码、请求体本身有问题
    ClientAbort,  // 客户端主动断连
}
```
主转发循环通过 `RequestForwarder::categorize_proxy_error()`（`forwarder.rs:1888`）将 `ProxyError` 映射为 `ErrorCategory`，再据此决定是继续故障转移（Retryable）还是直接返回（NonRetryable/ClientAbort）。
```

---

## F11 — `circuit_breaker.rs` struct line references are offset

**Location**: Ch4, lines 3991 and 4005

**Claim**:
- `CircuitBreaker`（`proxy/circuit_breaker.rs:76`）
- `AllowResult`（`circuit_breaker.rs:100`）

**Verdict**: ok

**Source evidence**: `circuit_breaker.rs:76` is `pub struct CircuitBreaker {`, `circuit_breaker.rs:100` is `pub struct AllowResult {`. Both correct.

**Severity**: n/a

---

## F12 — `RequestForwarder` struct shown twice with different field lists

**Location**: Ch4, lines 3696–3703 (first) and 4013–4032 (second)

**Claim (first, line 3696)**: Shows `RequestForwarder` with only 4 fields: `router`, `status`, `current_providers`, `max_attempts`.
**Claim (second, line 4013)**: Shows `RequestForwarder` with all 15 fields.

**Verdict**: ambiguous

**Source evidence**: `src-tauri/src/proxy/forwarder.rs:89-122` defines the struct with 15 fields. The first occurrence at line 3696 is a simplified view that omits 11 fields (`gemini_shadow`, `codex_chat_history`, `failover_manager`, `app_handle`, `current_provider_id_at_start`, `session_id`, `session_client_provided`, `rectifier_config`, `optimizer_config`, `copilot_optimizer_config`, `non_streaming_timeout`, `streaming_first_byte_timeout`). This is not flagged as simplified in the notes.

**Severity**: low

**Replacement**: Either remove the first occurrence (lines 3696–3703) since the second at lines 4013–4032 is complete, or add a note that the first is abbreviated.

---

## Summary

| # | Severity | Verdict | Issue |
|---|----------|---------|-------|
| F1 | medium | wrong | Duplicate `### 4.3` heading |
| F2 | medium | wrong | Duplicate `ClientFormat` enum block |
| F3 | low | wrong | Duplicate session module description |
| F4 | **high** | wrong | Error classification misrepresented as ≥500/<500; actual logic is status-code-specific with many 4xx being Retryable |
| F5 | low | stale | `session.rs` line count 627 → 626 |
| F6 | low | stale | `sse.rs` line count 346 → 345 |
| F7 | low | stale | `provider_router.rs` line count inconsistent (523 vs 524) |
| F8 | medium | wrong | `ProxyError` enum listing truncated, missing 10 of 20 variants and unclosed code block |
| F9 | medium | ambiguous | Stop flow omits 5-second timeout and misattributes `running=false` |
| F10 | medium | ambiguous | `ErrorCategory` three-state system omitted entirely |
| F11 | n/a | ok | CircuitBreaker/AllowResult line refs correct |
| F12 | low | ambiguous | `RequestForwarder` shown twice, first time with incomplete field list |
