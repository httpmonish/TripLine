# Wording Allowlist (R7 / R10 Forbidden Terminology)

This document defines the explicit allowlist for files that are permitted to mention forbidden terminology keywords (`tamper-proof`, `unbreakable`, `zero-trust`, `prevents all prompt injection`, `military-grade`, `AI-powered security`).

These files mention the terms solely to define enforcement rules, document audit findings, or quote guidelines. They do **NOT** claim these attributes for Tripline.

## Allowed Files and Explanations

1. **`docs/WORDING_ALLOWLIST.md`**: Defines this allowlist and quotes the terms for auditing.
2. **`scripts/repo_audit.py`**: Automated audit script that scans the repository for prohibited marketing filler.
3. **`docs/phase4_truth_audit.md`**: Audit table documenting the search and removal of overclaims.
4. **`docs/phase4_report.md`**: Phase 4 final report summarizing the terminology scan results.
5. **`docs/phase3_report.md`**: Phase 3 report referencing the prompt instructions.
6. **`docs/disclosure_snippets.md`**: Reference snippets documenting prompt rules.
7. **`docs/phase5_report.md`**: Phase 5 final report summarizing the audit verification.

No other code, documentation, dashboard template, or marketing text in the repository may contain these terms.
