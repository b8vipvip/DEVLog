This repository uses GitHub Agent v4 for GitHub Actions governance.

When working on Actions failures or workflow files:
- Read `/.github/GITHUB_AGENT.md`, `/.github/ACTIONS_STRATEGY.md`, and `/AGENTS.md` when present.
- Check open `[GitHub Agent][AI Repair]` Issues, then inspect the referenced full Run logs and source commit.
- Distinguish deterministic test/config failures from transient Runner/network failures and jobless ghost runs.
- Never rerun deterministic assertion/compile/lint failures merely to clear a red status.
- Prefer Fast Gate -> Full Gate and path-aware heavy builds.
- High-frequency PRs may cancel superseded SHA runs; default-branch validation already in progress should normally finish.
- Release / Deploy / Publish are side-effectful and must not be blindly replayed.
- Use a dedicated repair branch/PR and run the original failing test plus regressions and Policy Check.
