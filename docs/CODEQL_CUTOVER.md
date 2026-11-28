# CodeQL advanced setup: controlled cutover

The six-language no-upload preflight [PR 88](https://github.com/GOD13emad/FreeNetHub/pull/88) on head `ab1139c5c7ccf5ade342deadfff1b0b48e705ca8` completed all 31 checks, including the six scanner jobs in [run 46099647159](https://github.com/GOD13emad/FreeNetHub/actions/runs/46099647159). This proves the build and analysis recipes for that source tree, not operational alert coverage. No findings count is inferred from the preflight.

The production workflow retains the qualified steps and uses explicit language categories. Pushes to main, pull requests against main, a weekly schedule and manual dispatch are defined. It is dormant unless the repository Actions variable `FNH_ADVANCED_CODEQL_ENABLED` is exactly `true`. Do not set this variable on an unreviewed branch. Default setup remains active until a coordinated transition; enabling the variable alone cannot bypass GitHub's default-setup upload restriction.

## Acceptance and activation order

1. Record the current main SHA, default setup state, query suite, schedule, language categories, latest successful analysis SHAs and open alerts. Confirm the reviewed workflow is on main, the activation variable is absent/false, and protected branch checks remain intact.
2. Verify an authorized maintainer can change default setup and the repository variable, dispatch the exact main workflow and restore the previous setup. Do not start the cutover if any of these operations is unavailable.
3. In one coordinated maintenance window, disable default setup through GitHub's supported settings/API, read back the state, enable the repository variable and dispatch `codeql-advanced.yml` on main. This is not an atomic transaction: the interval until successful analysis upload is a coverage gap. Do not call migration complete until step 4.
4. Require all six jobs successful on the intended main SHA, non-error analyses with the expected categories, and actual uploaded results for each language. Inspect the tool status and extraction diagnostics. Reconcile alert identity and previous findings; never dismiss an alert merely because a category or workflow changed. Verify the scheduled/PR triggers and that the protected checks still apply.
5. If activation, dispatch, build, analysis, upload, permissions, or verification fails, stop the cutover. Disable the activation variable and restore the prior default configuration via the supported settings/API; read back configuration and verify renewed successful default analyses. Record the gap and the rollback result. A successful settings request alone does not prove restored scan coverage.

This runbook does not authorize disabling existing protection, merging a protected PR, or treating historical analysis as current main coverage. Preserve evidence and do not promote this change independently of the applicable review policy.

Official references: [Advanced setup](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configuring-advanced-setup-for-code-scanning), [Default setup](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/configure-code-scanning/configure-code-scanning), [Workflow configuration](https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options).
