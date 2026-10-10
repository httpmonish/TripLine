# Proposed MCP Changes — Addition of `label_issue` Tool

**Status**: NOT APPLIED (per Phase 1 Hard Constraint 3: `mcp/` is read-only).  
**Target Files**: `mcp/issues_mcp/tool.py` and `server.py`  
**Description**: The Phase 1 specification includes `label_issue(issue_id, label)` in the issue triage workflow. Currently, `mcp/issues_mcp/tool.py` provides `list_issues`, `read_issue`, and `comment_issue`, but lacks `label_issue`.

---

## 1. Proposed Diff for `mcp/issues_mcp/tool.py`

```diff
--- a/mcp/issues_mcp/tool.py
+++ b/mcp/issues_mcp/tool.py
@@ -86,3 +86,28 @@ def comment_issue(issue_id: str, text: str) -> str:
     res = f"comment added to {issue_id}"
     recorder.record_event(call_id, args_hash, "comment_issue", "execution_completed", result_hash=_hash_result(res), trace_id=trace_id)
     return res
+
+def label_issue(issue_id: str, label: str) -> str:
+    """Add a label to an issue."""
+    import uuid
+    from canary.state import get_current_run, get_current_trace, get_current_call
+    trace_id = get_current_trace() or None
+    call_id = get_current_call() or f"call-{uuid.uuid4().hex[:8]}"
+    args_hash = compute_args_hash("issues-mcp", "label_issue", {"issue_id": issue_id, "label": label})
+    recorder.record_event(call_id, args_hash, "label_issue", "received", trace_id=trace_id)
+    recorder.record_event(call_id, args_hash, "label_issue", "execution_started", trace_id=trace_id)
+    
+    if not ISSUES_FILE.exists():
+        res = "error: issues not found"
+        recorder.record_event(call_id, args_hash, "label_issue", "execution_completed", result_hash=_hash_result(res), trace_id=trace_id)
+        return res
+        
+    issues = json.loads(ISSUES_FILE.read_text())
+    for issue in issues:
+        if issue["id"] == issue_id:
+            if "labels" not in issue:
+                issue["labels"] = []
+            if label not in issue["labels"]:
+                issue["labels"].append(label)
+            ISSUES_FILE.write_text(json.dumps(issues, indent=2))
+            res = f"label '{label}' added to {issue_id}"
+            recorder.record_event(call_id, args_hash, "label_issue", "execution_completed", result_hash=_hash_result(res), trace_id=trace_id)
+            return res
+            
+    res = f"error: issue {issue_id} not found"
+    recorder.record_event(call_id, args_hash, "label_issue", "execution_completed", result_hash=_hash_result(res), trace_id=trace_id)
+    return res
```

---

## 2. Proposed Diff for `server.py`

```diff
--- a/server.py
+++ b/server.py
@@ -143,6 +143,11 @@ def comment_issue(issue_id: str, text: str) -> str:
     """Add a comment to an issue."""
     return issues_mod.comment_issue(issue_id, text)
 
+@mcp.tool()
+def label_issue(issue_id: str, label: str) -> str:
+    """Add a label to an issue."""
+    return issues_mod.label_issue(issue_id, label)
+
 @mcp.tool()
 def list_dir(path: str = ".") -> str:
     """List directory contents in the repository."""
```

---

## 3. Impact Assessment on Phase 1 Exit Gate

- **Achievability without modification**: **YES**. The core triage loop in Phase 1 can read issue queues (`list_issues`), inspect issue details (`read_issue`), examine repository source files (`read_file`), and post triage verdicts and labels via `comment_issue(issue_id, text)`.
- **Recommendation**: For Phase 1, preserve `mcp/` read-only integrity. The agent will record labels within triage comments via `comment_issue` until the human approves applying this diff for Phase 2.
