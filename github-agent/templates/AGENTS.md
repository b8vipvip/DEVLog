# Repository AI Instructions

This repository uses **GitHub Agent v4** for GitHub Actions governance and recovery.

Before changing CI/workflow behavior or repairing an Actions failure:

1. Read `/.github/GITHUB_AGENT.md` and `/.github/ACTIONS_STRATEGY.md` when present.
2. Check open Issues whose title starts with `[GitHub Agent][AI Repair]`.
3. Read the referenced workflow Run, complete job logs, source commit, and relevant code before editing.
4. Classify the failure before acting: deterministic test/config failure, transient infrastructure failure, ghost run, superseded run, or side-effectful release/deploy/publish.
5. Do not rerun deterministic pytest/assertion/compile/lint failures. They require a new fixing commit.
6. Work on a dedicated branch/PR unless the user explicitly requests a direct write.
7. Run the original failing test/job plus relevant regression tests and GitHub Agent Policy Check.
8. Keep PR concurrency replaceable for high-frequency PRs, but do not kill already-running default-branch validation merely because a newer push exists.
9. Prefer Fast Gate -> Full Gate and path-aware heavy builds.
10. Never blindly replay Release / Deploy / Publish side effects. A repository should have one final release authority.

## Ghost runs

A long-lived queued/in-progress run with no jobs, or a run that rejects normal cancellation while remaining active, is infrastructure state rather than a code failure. GitHub Agent v4 Governor uses normal cancel -> recheck -> force-cancel and does not create code Recovery for a jobless ghost run.

## AI Repair handoff

When a `[GitHub Agent][AI Repair]` Issue exists, treat it as an evidence package, not as a substitute for the full logs. Verify whether its source SHA has already been superseded before modifying code.

## CI baseline

New official actions should use the repository's current Node24-native baseline (for example checkout/setup-python/setup-node/upload-artifact current majors) unless compatibility requires otherwise.
