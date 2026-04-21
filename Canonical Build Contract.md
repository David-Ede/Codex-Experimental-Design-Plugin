# Canonical Build Contract: Codex DOE Scientific Toolchain

Date: 2026-04-20
Status: Canonical implementation contract

## 1. Purpose

This document is the source of truth for the actual build. If another planning document conflicts with this contract, this contract wins and the other document must be updated.

The build target is a local-first Codex plugin workflow for DOE and IVT/QbD analysis:

```text
Codex skill -> Python MCP server -> schema-valid artifacts -> React dashboard preview
```

Codex may orchestrate, explain, edit files, run commands, and open previews. Codex must not be the numerical source of truth.

## 2. Canonical Names

| Surface | Canonical Value |
|---|---|
| Plugin package | `doe-scientific-toolchain` |
| Primary skill | `scientific-study-designer` |
| MCP server name | `doe-scientific-toolchain` |
| Python package | `doe_toolchain` |
| Dashboard app | `apps/dashboard` |
| Study output root | `outputs/studies/` |
| Schema root | `schemas/` |
| Workflow fixture root | `fixtures/studies/` |
| Dashboard fixture root | `fixtures/dashboard/` |
| Validation reports | `validation-reports/` |

## 3. Canonical Repository Layout

```text
.
  .agents/
    plugins/
      marketplace.json
  .codex/
    config.toml.example
    local-environment.md
  plugins/
    doe-scientific-toolchain/
      .codex-plugin/
        plugin.json
      .mcp.json
      skills/
        scientific-study-designer/
          SKILL.md
          agents/
            openai.yaml
          references/
          scripts/
      assets/
  mcp-server/
    pyproject.toml
    src/
      doe_toolchain/
        server.py
        tools/
        science/
        ivt/
        economics/
        artifacts/
        validation/
        observability/
    tests/
  apps/
    dashboard/
  schemas/
  fixtures/
    studies/
    dashboard/
  scripts/
  outputs/
    studies/
  validation-reports/
  docs or root planning docs
```

## 4. Plugin and MCP Contract

`plugins/doe-scientific-toolchain/.codex-plugin/plugin.json` must use plugin-root-relative component paths:

```json
{
  "name": "doe-scientific-toolchain",
  "version": "0.1.0",
  "description": "Local DOE and IVT/QbD scientific toolchain for Codex with MCP-backed calculations and dashboard review.",
  "skills": "./skills/",
  "mcpServers": "./.mcp.json",
  "interface": {
    "displayName": "DOE Scientific Toolchain",
    "shortDescription": "Design DOE studies, fit response models, and review scientific dashboards.",
    "developerName": "DOE Toolchain Maintainers",
    "category": "Data",
    "capabilities": ["Read", "Write"]
  }
}
```

Development MCP setup is project-scoped and canonical:

```text
.codex/config.toml.example
```

The development MCP command must start the local package from the repository root, for example:

```toml
[mcp_servers.doe-scientific-toolchain]
command = "uv"
args = ["--directory", "mcp-server", "run", "python", "-m", "doe_toolchain.server"]
cwd = "."
startup_timeout_sec = 20
tool_timeout_sec = 120
```

Plugin-bundled `.mcp.json` may be enabled for distribution only after it is verified to be cache-safe. It must not depend on fragile relative paths from the installed plugin cache to the development repository.

## 5. Study Artifact Contract

Every study persists under:

```text
outputs/studies/<study_id>/
```

Canonical launch layout:

```text
study.json
factor_space.json
responses.json
constructs.json
imports/
designs/<design_id>/design_matrix.csv
designs/<design_id>/design_metadata.json
observations/endpoint_observations.csv
observations/endpoint_observations.metadata.json
observations/time_resolved_observations.csv
observations/time_resolved_observations.metadata.json
models/<fit_id>/model_fit.json
models/<fit_id>/residuals.csv
models/<fit_id>/predictions.csv
derived/endpoint_summary.json
derived/theoretical_yield.json
derived/effects.json
derived/prediction_grids.json
derived/economics.json
derived/recommendations.json
derived/verification_plan.json
dashboard_payload.json
audit_log.jsonl
```

Files are created only when relevant. Missing optional inputs must produce explicit unavailable states in `dashboard_payload.json`.

## 6. Launch Scope

Launch required:

```text
- local plugin package and scientific-study-designer skill
- project-scoped MCP setup
- Python MCP server with registered launch tools
- schemas and fixtures
- study persistence, hashing, audit logging, and safe path handling
- factor and response validation
- full factorial, two-level fractional factorial where supported, Latin hypercube, and candidate-set D-optimal selection
- D-optimal augmentation metadata foundation, not full iterative augmentation
- endpoint observation import
- time-resolved observation import and endpoint summary derivation
- construct registration
- theoretical yield and relative yield when inputs exist
- OLS response-surface model fitting
- effect summaries and prediction grids
- optional direct-input economics
- recommendation generation with reason codes and warnings
- launch-level verification planning
- dashboard payload generation
- React dashboard launch views
- no-cost and direct-cost end-to-end workflows
```

## 7. Launch Foundations With Unavailable States

Launch must represent these capabilities without claiming full support:

| Capability | Launch Behavior |
|---|---|
| Iterative augmentation | Store iteration and locked-row metadata; full selection against locked rows is paper-class. |
| Design-space probability | Store thresholds and prediction grids; Monte Carlo maps are unavailable until the paper-class tool runs. |
| Verification comparison | Store verification plan; observed comparison against prediction intervals is paper-class. |
| Construct transfer | Store and compare metadata; transfer predictions are paper-class. |
| Counterion DOE | Generic categorical factor support; specialized counterion analysis is paper-class. |
| Time-resolved modeling | Import and plot time courses; rich kinetic response models are paper-class. |

## 8. Paper-Class Scope

Paper-class support requires:

```text
- full locked-row D-optimal augmentation across at least three campaign iterations
- Monte Carlo design-space probability maps
- verification-result comparison against prediction intervals or acceptance limits
- time-resolved response modeling
- construct-transfer prediction with explicit assumptions
- counterion DOE analysis with categorical factor diagnostics
- multi-response desirability across yield, quality, relative yield, and optional cost efficiency
- paper-class dashboard views and validation report
```

## 9. Required Tool Inventory

Launch tools:

```text
create_or_update_study
validate_factor_space
design_doe
design_optimal_doe
import_endpoint_observations
import_time_resolved_observations
register_construct
calculate_theoretical_yield
fit_response_surface
analyze_effects
calculate_cogs_impact
suggest_next_experiment
plan_verification_runs
generate_dashboard_payload
launch_dashboard_preview
```

Paper-class tools:

```text
estimate_design_space_probability
compare_verification_results
transfer_construct_model
analyze_counterion_doe
fit_time_resolved_response_model
```

## 10. Technology Decisions

Backend:

```text
- Python 3.12 as primary, Python 3.11 supported if dependencies require it
- uv for reproducible local development
- FastMCP or current MCP Python SDK wrapper
- Pydantic v2 for runtime models
- JSON Schema 2020-12 for persisted contracts
- pandas, numpy, scipy, statsmodels, and scikit-learn only where method ownership is clear
- pytest, pytest-cov, and golden-output regression tests
```

Frontend:

```text
- Vite, React, TypeScript
- strict TypeScript
- schema-derived or shared dashboard payload types
- TanStack Table for dense matrix views if native table ergonomics are insufficient
- charting library chosen for SVG/Canvas exportability, deterministic rendering, and accessibility hooks
- Vitest for unit/component tests
- Playwright for browser smoke and visual-state tests
```

Quality:

```text
- formatting and linting are required before release
- all deterministic methods expose seed, method version, package versions, and tolerance
- every scientific output links to source artifacts
- dashboard does not perform scientific calculations
```

## 11. Validation Gates

Gate 0: repository and contract gate:

```text
- canonical layout exists
- plugin metadata validates
- MCP server starts
- launch tool registry matches this contract
- schema validator runs
- fixtures exist for valid and invalid launch inputs
- dashboard renders fixture payload
```

Gate 0 residual-risk closure requirements:

```text
1. Plugin/MCP smoke test:
   - plugins/doe-scientific-toolchain/.codex-plugin/plugin.json exists.
   - plugins/doe-scientific-toolchain/skills/scientific-study-designer/SKILL.md exists.
   - .agents/plugins/marketplace.json exposes the local plugin.
   - .codex/config.toml.example defines doe-scientific-toolchain MCP server.
   - doe_toolchain.server starts and exposes at least create_or_update_study as a no-op or skeleton tool.
   - Codex can discover the plugin, load the skill, start MCP, and call create_or_update_study.

2. Dependency lock:
   - mcp-server/pyproject.toml exists.
   - uv.lock exists after uv lock or uv sync.
   - package versions for mcp/FastMCP, pydantic, numpy, scipy, pandas, statsmodels, scikit-learn, jsonschema, and pytest are captured.
   - backend import/version smoke test passes from a clean uv sync.

3. Minimum schema set:
   - schemas/artifact_metadata.schema.json
   - schemas/warning.schema.json
   - schemas/error.schema.json
   - schemas/tool_envelope.schema.json
   - schemas/audit_log_entry.schema.json
   - schemas/study.schema.json
   - schemas/factor_space.schema.json
   - schemas/responses.schema.json
   - schemas/dashboard_payload.schema.json
   - scripts/validate_schemas.py validates valid fixtures and rejects invalid fixtures with stable error paths.

4. Minimum fixture set:
   - fixtures/studies/minimal_doe/study.json
   - fixtures/studies/minimal_doe/factor_space.json
   - fixtures/studies/minimal_doe/responses.json
   - fixtures/studies/minimal_doe/dashboard_payload.json
   - invalid study/factor/response fixtures for bad IDs, bad units, invalid bounds, duplicate normalized names, and missing required metadata.
   - fixtures/dashboard/empty_payload_state.json
   - fixtures/dashboard/phase0_design_only_payload.json
   - fixtures/dashboard/payload_validation_error.json
```

Gate 0 is not complete until all four residual-risk groups above pass.

Gate 1: launch gate:

```text
- no-cost workflow passes end to end
- direct-cost workflow passes end to end
- launch fixtures pass within tolerance
- dashboard desktop, tablet, and mobile smoke tests pass
- all launch schemas validate
- every derived artifact has hashes, method version, tool version, warnings, and audit entry
- security tests pass for path handling, CSV safety, and dashboard escaping
```

Gate 2: paper-class gate:

```text
- paper-class tools pass contract tests
- three-iteration augmentation fixture passes
- Monte Carlo design-space fixture passes
- verification comparison fixture passes
- construct-transfer and counterion fixtures pass
- paper-class dashboard views pass browser tests
- paper-class validation report records limitations and pass/fail status
```

## 12. Traceability Rule

Every implementation ticket must map to:

```text
PRD requirement -> MCP tool or dashboard component -> schema artifact -> fixture -> automated test -> release gate
```

No feature is complete until this mapping exists and its gate passes.

## 13. Final Build Rule

The product is production-grade only when a reviewer can reproduce every displayed scientific result from source inputs, schema-valid artifacts, method versions, package versions, warnings, and audit logs. Anything without complete provenance is unavailable or invalid, not merely undocumented.

## 14. Workbench Redesign Addendum

The next product direction is a study-object-first workbench, not a chat-first dashboard. The current plugin, MCP, artifact, and React architecture remains valid, but the React surface becomes the primary experiment strategy workspace.

Canonical workbench shape:

```text
Codex skill -> MCP tools -> schema-valid study artifacts -> workbench payload -> React workbench
```

Required workbench concepts:

```text
- study setup state
- recommendation mode
- candidate design sets
- candidate design capability diagnostics
- can learn / cannot learn summaries
- design comparisons
- contextual AI panels with source refs
- stale-state indicators
- committed run plans
- study snapshots
```

The first build slice is the Workbench Candidate Comparison Slice:

```text
1. Add workbench schemas and fixtures.
2. Render candidate design cards.
3. Render a side-by-side design comparison table.
4. Render a right-rail AI advisor panel.
5. Require source refs for AI explanation panels.
```

The technical directory may remain `apps/dashboard` during migration. User-facing language should move toward "Workbench", "Study Setup", "Candidate Designs", "Compare", "Run Plan", and "AI Advisor".

New schema files introduced for the workbench foundation:

```text
learnability_summary.schema.json
candidate_design.schema.json
candidate_design_set.schema.json
design_comparison.schema.json
run_plan_commit.schema.json
study_snapshot.schema.json
stale_state.schema.json
contextual_ai_panel.schema.json
workbench_payload.schema.json
```

The dashboard payload may include an optional `workbench` section. Existing dashboard payloads remain valid while the workbench migration proceeds.
