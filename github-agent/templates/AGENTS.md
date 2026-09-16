# Repository AI Instructions

This repository uses **GitHub Agent v4** for GitHub Actions governance and recovery.

Before changing CI/workflow behavior or repairing an Actions failure:
1. Read `/.github/GITHUB_AGENT.md` and `/.github/ACTIONS_STRATEGY.md` when present.
2. Check open Issues whose title starts with `[GitHub Agent][AI Repair]`, then read the referenced full Run logs and source commit.
3. Classify the failure: deterministic test/config, transient infrastructure, ghost, superseded, or side-effectful.
4. Do not rerun deterministic pytest/assertion/compile/lint failures; create a fixing commit.
5. Work on a dedicated branch/PR unless the user explicitly requests a direct write.
6. Run the original failing test/job plus relevant regressions and Policy Check.
7. Prefer Fast Gate -> Full Gate and path-aware heavy builds.
8. High-frequency PRs may cancel superseded SHA runs; default-branch validation already in progress should normally finish.
9. Never blindly replay Release / Deploy / Publish side effects; keep one final release authority.

A long-lived queued/in-progress run with no jobs, or a run that rejects normal cancellation while remaining active, is infrastructure state rather than a code failure. GitHub Agent v4 Governor uses normal cancel -> recheck -> force-cancel and does not create code Recovery for a jobless ghost run.
