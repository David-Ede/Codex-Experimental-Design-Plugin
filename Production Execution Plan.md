# Production Execution Plan: Codex DOE Scientific Toolchain

Date: 2026-04-20
Status: Build execution plan

## 1. Build Objective

Ship a production-grade local-first Codex scientific toolchain that can:

```text
1. Create a DOE/IVT study.
2. Generate a validated DOE.
3. Import endpoint and time-resolved observations.
4. Calculate IVT theoretical and relative yield when inputs exist.
5. Fit response-surface models and expose diagnostics.
6. Calculate optional direct-input economics without blocking no-cost workflows.
7. Recommend next experiments and launch-level verification runs.
8. Render a trustworthy React dashboard from schema-valid payloads.
9. Produce a validation report proving reproducibility, provenance, and fail-safe behavior.
```

The first production-quality release is Gate 1 launch readiness. Paper-class IVT/QbD work starts only after Gate 1 is stable.

## 2. Engineering Standards

Backend standards:

```text
- Python package managed with uv.
- Strict type hints on public functions.
- Pydantic models at tool boundaries.
- JSON Schema validation for persisted artifacts.
- Deterministic seeds for stochastic methods.
- Structured error and warning codes.
- Append-only audit events for every tool call.
- No network calls in launch scientific runtime.
```

Frontend standards:

```text
- Vite + React + TypeScript.
- Strict TypeScript.
- Runtime payload validation before render.
- Accessible keyboard navigation for tabs, filters, tables, and drawers.
- Responsive states for 1440x900, 1024x768, and 390x844.
- No scientific recomputation in React.
- Playwright screenshots for launch fixture states.
```

Release standards:

```text
- One command runs backend tests.
- One command runs schema validation.
- One command runs dashboard tests.
- One command runs launch E2E workflow.
- One command generates validation report.
- No generated private study outputs are packaged.
```

## 3. Phase Plan

### Phase 0: Contract Freeze

Goal:

```text
Turn planning into buildable contracts before code starts.
```

Tasks:

```text
1. Adopt Canonical Build Contract.md as source of truth.
2. Update conflicting docs to match canonical names, paths, and scope.
3. Create initial traceability matrix template.
4. Define release gates in CI/local scripts.
```

Exit criteria:

```text
- no unresolved path/name/scope conflicts in planning docs
- launch vs paper-class scope is unambiguous
- execution plan is approved for implementation
```

### Phase 1: Repository Skeleton and Tooling

Goal:

```text
Create a repo that installs, starts, validates, and tests from a clean checkout.
```

Tasks:

```text
1. Create canonical directories.
2. Add pyproject.toml for mcp-server.
3. Add package.json and pnpm workspace.
4. Add .codex/config.toml.example.
5. Add plugin manifest, skill skeleton, and local marketplace entry.
6. Add formatting, linting, test, and validation commands.
7. Add minimal schemas required for Gate 0 validation.
8. Add minimal valid and invalid fixtures required for Gate 0 validation.
9. Add placeholder MCP tool registry with every launch tool name and a callable create_or_update_study skeleton.
10. Add dependency lockfiles.
11. Add CI workflow or local equivalent script.
```

Exit criteria:

```text
- Python package imports as doe_toolchain
- MCP server starts and registers placeholder launch tools
- dashboard app starts from fixture payload
- plugin appears through repo-local marketplace
- Codex can discover the plugin, load the skill, start MCP, and call create_or_update_study
- uv sync from a clean checkout produces a locked backend environment
- schema validation passes good fixtures and fails known-bad fixtures for expected reasons
- Gate 0 skeleton checks pass
```

Phase 1 residual-risk work items:

```text
- Plugin/MCP smoke: prove the local Codex plugin and project-scoped MCP server can be used together.
- Dependency lock: pin and record backend and dashboard package versions before scientific outputs exist.
- Minimum schemas: implement the first schema set before adding algorithms.
- Minimum fixtures: create known-good and known-bad fixtures before writing feature tests.
```

### Phase 2: Data Contracts and Persistence

Goal:

```text
Make artifacts durable, schema-valid, hashable, auditable, and safe before scientific algorithms are added.
```

Tasks:

```text
1. Implement schemas for study, factor space, responses, tool envelope, warnings, errors, audit event, and dashboard shell.
2. Implement artifact path resolver with canonical path and symlink protection.
3. Implement write_new_run overwrite policy.
4. Implement hash generation.
5. Implement append-only audit logger.
6. Implement create_or_update_study and validate_factor_space.
7. Add valid and invalid fixtures.
```

Exit criteria:

```text
- schema validation fails with precise paths
- path traversal tests fail safely
- every placeholder and real tool call writes one audit event
- dashboard can render a study shell
```

### Phase 3: DOE Generation

Goal:

```text
Generate deterministic, diagnostically useful DOE matrices from validated factor spaces.
```

Tasks:

```text
1. Implement factor encoding and transforms.
2. Implement full factorial and two-level fractional factorial where supported.
3. Implement Latin hypercube sampling.
4. Implement candidate-set generation.
5. Implement candidate-set D-optimal selection.
6. Implement launch augmentation metadata, not full locked-row augmentation.
7. Write design matrix and metadata artifacts.
8. Add fixed-seed golden tests.
```

Exit criteria:

```text
- valid DOE requests produce schema-valid artifacts
- infeasible constraints fail safely
- rank and condition diagnostics are present
- equivalent D-optimal designs are tested by criterion/rank unless selected indices are pinned
```

### Phase 4: Observation Import and IVT Foundations

Goal:

```text
Accept observed scientific data without losing provenance or over-interpreting incomplete inputs.
```

Tasks:

```text
1. Implement endpoint CSV/JSON/inline import.
2. Preserve original column names, source rows, raw values, and units.
3. Implement time-resolved long-format import.
4. Implement endpoint summary derivation from time courses.
5. Implement construct registration.
6. Implement sequence/composition parsing.
7. Implement theoretical and relative yield.
```

Exit criteria:

```text
- clean endpoint and timecourse fixtures import
- invalid units and unknown run IDs fail or warn as specified
- theoretical yield matches hand fixtures
- relative yield remains unavailable until measured and theoretical yield exist
```

### Phase 5: Modeling and Effects

Goal:

```text
Fit response-surface models with diagnostics that prevent false confidence.
```

Tasks:

```text
1. Implement model term parser and heredity checks.
2. Build encoded model matrix.
3. Fit OLS models.
4. Detect rank deficiency, high condition number, leverage, residual outliers, and insufficient degrees of freedom.
5. Implement R2, adjusted R2, RMSE, and cross-validated predictive score where valid.
6. Generate residual and prediction artifacts.
7. Generate effects, Pareto payloads, factor-response curves, and contour grids.
```

Exit criteria:

```text
- coefficient fixtures pass within tolerance
- over-parameterized models fail safely
- weak models block or warn before recommendations
- effect payloads are dashboard-ready and schema-valid
```

### Phase 6: Optional Economics, Recommendations, and Verification

Goal:

```text
Add decision support without making unsupported cost or optimization claims.
```

Tasks:

```text
1. Implement direct component-cost validation.
2. Implement cost by condition and cost efficiency.
3. Ensure no-cost workflow skips economics cleanly.
4. Implement recommendation scoring with constraints, objectives, and reason codes.
5. Implement launch-level verification planning around optimum, center, corners, and quality boundaries when available.
6. Add unsupported-claim tests for cost savings and verification language.
```

Exit criteria:

```text
- missing costs never block DOE/modeling/dashboard
- mixed currencies fail without conversion artifact
- recommendations cite model status and constraints
- verification plan does not imply verification results
```

### Phase 7: Dashboard Launch Surface

Goal:

```text
Make the scientific state hard to misread.
```

Tasks:

```text
1. Generate dashboard payload from persisted artifacts only.
2. Add runtime payload validation.
3. Implement Overview, Matrix, Time Courses, Effects, Relative Yield, Economics, Recommendations, Verification, and Diagnostics tabs.
4. Add warning strip, unavailable states, source badges, unit labels, and artifact links.
5. Add responsive layouts and accessibility behavior.
6. Add Playwright tests for all launch dashboard fixtures.
```

Exit criteria:

```text
- valid payload renders all launch tabs
- invalid payload shows diagnostics instead of blank screen
- no-cost economics state is visually distinct from errors
- desktop, tablet, and mobile smoke tests pass
- dashboard does not calculate scientific results
```

### Phase 8: Launch Hardening

Goal:

```text
Prove the launch slice is reproducible, safe, and usable.
```

Tasks:

```text
1. Run no-cost E2E workflow.
2. Run direct-cost E2E workflow.
3. Run platform smoke test: plugin install, skill discovery, MCP discovery, one tool call, dashboard preview.
4. Generate validation report with hashes, package versions, method versions, warnings, and test outcomes.
5. Review generated outputs for private data leakage.
6. Freeze launch limitations.
```

Exit criteria:

```text
- Gate 1 passes
- all Severity 0 and Severity 1 defects are fixed
- launch validation report is committed or attached to release artifact
- release notes state known limitations
```

### Phase 9: Paper-Class Expansion

Goal:

```text
Expand only after the launch contract is stable.
```

Tasks:

```text
1. Implement full locked-row D-optimal augmentation.
2. Implement Monte Carlo design-space probability.
3. Implement verification result comparison.
4. Implement time-resolved response modeling.
5. Implement construct-transfer predictions with assumptions.
6. Implement counterion DOE analysis.
7. Implement multi-response desirability.
8. Add paper-class dashboard views.
9. Generate Gate 2 validation report.
```

Exit criteria:

```text
- Gate 2 passes
- paper-class claim is allowed
- final summary distinguishes explored, modeled, optimized, recommended, verified, and unavailable claims
```

## 4. Initial Ticket Breakdown

| ID | Title | Phase | Depends On | Done Signal |
|---|---|---:|---|---|
| B-001 | Create canonical repo skeleton | 1 | Phase 0 | directories and package files exist |
| B-002 | Add local plugin package | 1 | B-001 | plugin metadata validates |
| B-003 | Add MCP config and placeholder server | 1 | B-001 | server starts and lists launch tools |
| B-004 | Add dashboard shell | 1 | B-001 | fixture payload renders |
| B-005 | Lock backend and dashboard dependencies | 1 | B-001 | uv.lock and pnpm lockfile exist; version capture test passes |
| B-006 | Add minimum Gate 0 schema set | 1 | B-001 | required schemas exist |
| B-007 | Add minimum Gate 0 fixtures | 1 | B-006 | good and bad fixtures exist |
| B-008 | Implement schema validator | 1 | B-006, B-007 | valid/invalid fixtures tested |
| B-009 | Run Plugin/MCP smoke test | 1 | B-002, B-003 | Codex can call create_or_update_study |
| B-010 | Implement artifact store | 2 | B-008 | path traversal and hash tests pass |
| B-011 | Implement audit logger | 2 | B-010 | success/failure/skipped events tested |
| B-012 | Implement study and factor tools | 2 | B-011 | study/factor fixtures pass |
| B-013 | Implement DOE engine | 3 | B-012 | fixed-seed DOE fixtures pass |
| B-014 | Implement observation import | 4 | B-013 | endpoint/timecourse fixtures pass |
| B-015 | Implement construct and yield tools | 4 | B-014 | sequence/yield fixtures pass |
| B-016 | Implement model fitting | 5 | B-014 | coefficient/diagnostic fixtures pass |
| B-017 | Implement effects payloads | 5 | B-016 | effect and grid fixtures pass |
| B-018 | Implement optional economics | 6 | B-014 | no-cost and with-cost tests pass |
| B-019 | Implement recommendations and verification planning | 6 | B-017, B-018 | reason-code and verification fixtures pass |
| B-020 | Implement dashboard payload generator | 7 | B-015, B-017, B-019 | payload validates |
| B-021 | Implement launch dashboard tabs | 7 | B-020 | Playwright launch views pass |
| B-022 | Implement launch E2E workflows | 8 | B-021 | Gate 1 workflow tests pass |
| B-023 | Generate validation report | 8 | B-022 | report records Gate 1 decision |

## 5. CI and Local Commands

Target commands:

```powershell
uv --directory mcp-server run pytest
uv --directory mcp-server run pytest --run-regression
uv --directory mcp-server run python ..\scripts\validate_schemas.py
pnpm --dir apps/dashboard install --frozen-lockfile
pnpm --dir apps/dashboard typecheck
pnpm --dir apps/dashboard test
pnpm --dir apps/dashboard build
pnpm --dir apps/dashboard test:e2e
python scripts/run_launch_workflow.py --fixture fixtures/studies/ivt_launch_no_costs
python scripts/run_launch_workflow.py --fixture fixtures/studies/ivt_launch_with_costs
python scripts/run_validation_report.py --scope launch
```

## 6. Production Risks and Controls

| Risk | Control |
|---|---|
| Scope creep into paper-class before launch | Canonical scope table and Gate 1 lock. |
| Plugin MCP path breaks from installed cache | Project-scoped MCP config for development; cache-safe bundled MCP only after verification. |
| Codex invents scientific values | Skill rules, tool-only numerical outputs, artifact citations in summaries. |
| Dashboard implies unavailable analysis is zero or successful | Explicit unavailable-state fixtures and screenshot tests. |
| Weak model drives recommendations | Blocking warnings for rank deficiency and weak predictive scores. |
| Cost analysis becomes hidden dependency | No-cost E2E workflow is release-blocking. |
| Sensitive local data leaks | Local-only runtime, no network calls, log redaction, output packaging checks. |
| Schema drift | Schema-first fixtures, generated types where feasible, payload validation in backend and frontend. |

## 7. Definition of Done

A feature is done only when:

```text
- requirement mapping exists
- schema exists or existing schema is confirmed
- implementation writes artifacts and audit events
- warnings and errors use registered codes
- unit and contract tests pass
- dashboard state exists when user-visible
- documentation and fixtures are updated
- validation gate impact is known
```

The build is production-grade when Gate 1 passes repeatedly from a clean checkout and a reviewer can trace every dashboard value to source artifacts and method versions.
