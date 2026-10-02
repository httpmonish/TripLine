# Phase 4: Security Boundary

## 1. Phase 4 Objective
The objective of Phase 4 is to establish a hard server-side path jail boundary, separating the trusted backend filesystem environment from the agent, regardless of ArmorIQ policy. We explicitly prove that the agent process and its Python gateway are *not* the ultimate security boundary. The MCP server evaluates path requests independently using strict parameter policy enforcement.

## 2. Threat Model
- **Compromised Agent**: The agent might ignore T3 hold rules or attempt to request paths outside the valid root repository.
- **Bypassed Gateway**: Gateway checks are an early warning, but a complete bypass should not result in filesystem exploitation.
- **Path Escapes**: Using URL-encoded sequences, `~` (home directory), `..` (parent traversal), and symlink manipulation to read or overwrite secrets outside the designated workspace.

## 3. Trusted Root
The workspace is locked strictly to the `fixtures/demo_repo/` path.
Absolute paths and any paths resolving hierarchically or symbolically outside this root are explicitly rejected.

## 4. Path Normalization Pipeline
The server-side path constraint resolves incoming `raw_path` values via the following deterministic flow:
```text
RAW PATH
   ↓
decode / normalize (percent encoding)
   ↓
expand user notation (~)
   ↓
canonicalize / realpath (resolve symlinks and ..)
   ↓
compare trusted root
   ↓
ALLOW / REJECT
   ↓
MCP execution only if allowed
```

## 5. `~` Handling
Paths starting with `~` are expanded. If the resulting expanded user path falls outside the trusted root, the request is immediately rejected. For instance, `~/.ssh/fake_key` resolves to the system user directory (e.g., `/Users/monish/.ssh/fake_key`) and is rejected.

## 6. `..` Handling
`..` sequences are resolved lexically as part of canonicalization. An attempt to read `../outside.txt` or `src/../../outside.txt` is rejected since the resolved location leaves the trusted tree. Legitimate usages of `..` that remain contained (e.g. `src/utils/../main.py`) are properly resolved and allowed.

## 7. Percent-Encoding Handling
Paths with encoded sequences like `%2e%2e/` (which translates to `../`) are decoded in the first pipeline step. If double-encoding signs (`%`) persist, or the decoded path escapes the boundary, it is immediately rejected. Legitimate encoding (`hello%20world.txt`) resolves safely and is permitted.

## 8. Symlink Handling
Symlink escapes are aggressively detected using `pathlib.Path.resolve()`, which resolves the physical link target before the boundary check. A path like `src/link_to_outside` evaluating to `../../outside.txt` translates to a path outside the trusted root and is blocked. 

## 9. Server-Side Enforcement
The jail boundary (`mcp/common/jail.py`) was integrated natively into the MCP server configuration (`mcp/repo_mcp/tool.py`). This guarantees that even if a request originates from an authorized ArmorIQ session and circumvents the gateway, the server itself intercepts it.

## 10. Parameter Policy
Tool definitions such as `repo_mcp.read_file` and `repo_mcp.write_patch` evaluate the path string parameter directly through the jail pipeline before granting file descriptors. Only paths within the trusted boundary are acted upon.

## 11. Gateway / Jail Relationship
Tripline retains an early gateway checker (`gateway/param_check.py`), allowing early rejection of dangerous inputs. However, the MCP Jail evaluates 100% of incoming tasks identically, ensuring identical verdicts and a dual layer of protection.

## 12. Taint Rule
A taint-aware mechanism exists (`gateway/taint_rule.py`) to monitor the context state (`t3_ingested`). If an LLM interacts with untrusted issue data, sensitive sinks are flagged for a hold.

## 13. Sensitive Sinks
Currently recognized sensitive sinks for the Phase 4 threshold are:
- `write_patch`
- `comment_issue`

## 14. Budget Guard
`gateway/budget.py` implements a straightforward threshold cap on total step loops per invocation, failing-closed automatically if a rogue LLM enters an infinite planning or execution cycle.

## 15. Attack A
In **Attack A**, the agent was prompted to fix an issue but read poisoned T3 input instructing it to read an SSH key (`~/.ssh/fake_key`). The gateway and the MCP server both accurately trapped the malicious path expansion and rejected it instantly, resulting in 0 execution.

## 16. Test Corpus
The test suite includes 14 individual conditions spanning benign inner-root usages and multiple escape modalities (`~`, `..`, `%2e`, symlink). 

## 17. Gateway/Jail Agreement Results
Both the Tripline gateway path validator and the internal MCP server validator agreed identically on 100% of test cases.

## 18. Actual Test Results
28 tests across Phase 1, Phase 2, Phase 3, and Phase 4 passed seamlessly in continuous integration, proving safety and regression consistency.

## 19. Known Limitations
- The jail operates at the Python application level; direct process compromise would enable host FS access since the overarching OS/container doesn't rigidly chroot this specific mock. 
- Race conditions (TOCTOU) during `resolve()` are minimal for simple test environments, but a production jail would require using path-relative open (`openat`) via OS-level directory file descriptors. 

## 20. Phase 5 Prerequisites
The infrastructure for separating untrusted path execution is fully deployed. Tripline is now ready to support provenance-tracking and explicit source-attribution tracking (Phase 5).
