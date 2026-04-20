# Packaging & Setup Guide: Codex Scientific Toolchain

Date: 2026-04-20
Status: Draft for implementation planning
Related documents:

```text
- Technical Architecture Brief.md
- Product Requirements Document.md
- MCP Tool API Spec.md
- Dashboard UX Spec.md
- Validation & Test Plan.md
- Implementation Roadmap.md
- Security & Provenance Plan.md
- Canonical Build Contract.md
- Production Execution Plan.md
```

## 1. Purpose

This guide defines how the Codex Scientific Toolchain should be packaged, installed, configured, run, tested, and released as a local Codex plugin.

It is written as the target setup contract for the implementation. The repository should be built so that a developer can follow this guide from a clean checkout and reach a working local plugin with:

```text
- Python MCP scientific backend
- React dashboard preview
- Codex skill instructions
- schema and fixture validation
- local launch workflow tests
```

## 2. Package Model

The project should be packaged as a single local plugin repository containing:

```text
- Codex plugin metadata
- Codex skill instructions
- Python MCP server
- scientific engine modules
- JSON schemas
- fixture studies
- React dashboard app
- validation scripts
- planning documents
```

Launch packaging is local-first. It does not require:

```text
- hosted backend
- hosted database
- authentication provider
- reagent price API
- LIMS connection
- ELN connection
- cloud deployment
```

## 3. Repository Layout

Target repository layout:

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
      assets/
  mcp-server/
    pyproject.toml
    README.md
    src/
      doe_toolchain/
        __init__.py
        server.py
        tools/
        science/
        ivt/
        economics/
        artifacts/
        schemas/
    tests/
  apps/
    dashboard/
      package.json
      src/
      tests/
  schemas/
    study.schema.json
    factor_space.schema.json
    responses.schema.json
    design.schema.json
    observations.schema.json
    construct.schema.json
    theoretical_yield.schema.json
    model_fit.schema.json
    effects.schema.json
    economics.schema.json
    recommendations.schema.json
    verification.schema.json
    dashboard_payload.schema.json
    audit_event.schema.json
  fixtures/
    studies/
  scripts/
    validate_schemas.py
    run_launch_workflow.py
    run_validation_report.py
  outputs/
    studies/
  validation-reports/
  docs/
  Canonical Build Contract.md
  Production Execution Plan.md
  Product Requirements Document.md
  Scientific Methods Spec.md
  Data & Schema Contract.md
  MCP Tool API Spec.md
  IVT QbD Workflow Spec.md
  Dashboard UX Spec.md
  Validation & Test Plan.md
  Implementation Roadmap.md
  Security & Provenance Plan.md
  Packaging & Setup Guide.md
```

## 4. Prerequisites

Required local software:

```text
- Python 3.11 or 3.12
- Node.js 20 LTS or newer
- pnpm 9 or newer
- uv
- Git
- Codex desktop or Codex CLI with local plugin support
```

Recommended local software:

```text
- PowerShell 7 on Windows
- VS Code or equivalent editor
- Playwright browser dependencies for dashboard smoke tests
```

Python package families expected:

```text
- MCP Python SDK or FastMCP-compatible server framework
- Pydantic v2 or equivalent validation layer
- numpy
- scipy
- pandas
- statsmodels or scikit-learn where method requirements fit
- JSON Schema 2020-12 validator
- pytest
```

Dashboard package families expected:

```text
- React
- TypeScript
- Vite
- charting library for dense scientific plots
- table/grid library if native tables become insufficient
- Playwright
- Vitest or equivalent component test runner
```

The implementation should pin exact package versions in lockfiles before release.

## 5. Local Setup

### 5.1 Clone or Open Repository

Open the repository root:

```powershell
cd "C:\Users\David\Desktop\Codex Plugins\DOE"
```

When the implementation is created in a different location, run all commands from that repository root.

### 5.2 Python Environment

Use `uv` for the canonical development environment:

```powershell
uv --directory mcp-server sync --all-extras --dev
uv --directory mcp-server run python -c "import doe_toolchain"
```

Fallback when `uv` is unavailable:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .\mcp-server[dev]
```

Expected result:

```text
- Python imports doe_toolchain successfully.
- MCP server package installs in editable mode.
- Test dependencies are available.
```

### 5.3 Dashboard Dependencies

Install dashboard dependencies:

```powershell
pnpm --dir apps/dashboard install
```

Expected result:

```text
- apps/dashboard/pnpm-lock.yaml exists.
- dashboard dependencies install without peer dependency failures.
```

### 5.4 Browser Test Dependencies

Install Playwright browsers:

```powershell
pnpm --dir apps/dashboard exec playwright install
```

Expected result:

```text
- Chromium browser is available for dashboard smoke tests.
```

## 6. Plugin Metadata

The plugin metadata file must exist at:

```text
plugins/doe-scientific-toolchain/.codex-plugin/plugin.json
```

Required metadata fields:

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
    "capabilities": ["Read", "Write"],
    "defaultPrompt": [
      "Use DOE Scientific Toolchain to create an IVT QbD study.",
      "Use DOE Scientific Toolchain to fit observed DOE data and refresh the dashboard."
    ]
  }
}
```

Packaging rules:

```text
- plugin name uses lowercase kebab-case
- plugin version uses semantic versioning
- manifest component paths are plugin-root-relative and start with ./
- .mcp.json is a pointer to MCP configuration, not an inline server definition
- active development uses .codex/config.toml.example as the canonical local MCP setup
- plugin-bundled MCP must use a cache-safe command, such as an installed console script, before release
- plugin metadata does not include secrets
```

MCP configuration split:

```text
- .codex/config.toml.example is the authoritative development MCP setup.
- plugins/doe-scientific-toolchain/.mcp.json is a distribution artifact.
- Do not point .mcp.json at repo-relative backend paths unless the plugin is installed from that same repo path and the behavior has been smoke-tested.
- Before release, verify that Codex can discover the MCP server from a clean local plugin install.
```

## 7. Codex Skill Packaging

The Codex skill must exist at:

```text
plugins/doe-scientific-toolchain/skills/scientific-study-designer/SKILL.md
```

The skill must instruct Codex to:

```text
- use MCP tools for numerical scientific outputs
- create or select a study before analysis
- validate factor space before DOE generation
- import observations before model fitting
- calculate theoretical and relative yield only when required construct and NTP inputs exist
- calculate COGS only when direct component costs are supplied
- continue without COGS when costs are absent
- generate dashboard payloads before launching dashboard preview
- surface warnings and unavailable states in user-facing explanations
- avoid claiming paper-class analysis support unless the required tools and validation gates exist
```

The skill must not instruct Codex to:

```text
- infer reagent costs
- fetch reagent prices
- calculate model coefficients manually in natural language
- treat dashboard charts as source data
- hide sparse-design or rank-deficiency warnings
```

## 8. MCP Server Setup

### 8.1 Start MCP Server Directly

Development command:

```powershell
python -m doe_toolchain.server
```

Expected result:

```text
- server starts without import errors
- launch tools are registered
- startup logs show package version and schema version
```

### 8.2 Required MCP Tools

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

Post-launch or paper-class expansion tools:

```text
estimate_design_space_probability
compare_verification_results
transfer_construct_model
analyze_counterion_doe
fit_time_resolved_response_model
```

Tool registration must match MCP Tool API Spec.md.

### 8.3 Server Configuration

Launch configuration should be file-based and local:

```text
mcp-server/config/defaults.json
```

Required settings:

```json
{
  "outputs_root": "../outputs/studies",
  "schema_root": "../schemas",
  "fixture_root": "../fixtures",
  "dashboard_app_root": "../apps/dashboard",
  "allow_network_at_runtime": false,
  "default_overwrite_policy": "write_new_run",
  "strict_validation_default": true
}
```

Configuration rules:

```text
- paths are resolved relative to the repository root
- unsafe path escapes are rejected
- runtime network access defaults to false
- no API keys are required for launch workflows
```

## 9. Dashboard Setup

### 9.1 Start Dashboard

Development command:

```powershell
pnpm --dir apps/dashboard dev
```

Expected result:

```text
- dashboard dev server starts on localhost
- dashboard can load a fixture dashboard_payload.json
- no blocking console errors occur
```

### 9.2 Build Dashboard

Build command:

```powershell
pnpm --dir apps/dashboard build
```

Expected result:

```text
- production build succeeds
- TypeScript compilation succeeds
- dashboard assets are generated under the configured build output directory
```

### 9.3 Dashboard Data Contract

The dashboard receives one generated payload:

```text
outputs/studies/<study_id>/dashboard_payload.json
```

Dashboard rules:

```text
- render payload data
- validate payload version
- show incompatible payload state for unsupported versions
- show unavailable states
- show warnings
- avoid scientific recalculation
- avoid writing study artifacts
```

## 10. Schema Setup

Minimum Gate 0 schemas:

```text
schemas/artifact_metadata.schema.json
schemas/warning.schema.json
schemas/error.schema.json
schemas/tool_envelope.schema.json
schemas/audit_log_entry.schema.json
schemas/study.schema.json
schemas/factor_space.schema.json
schemas/responses.schema.json
schemas/dashboard_payload.schema.json
```

Schema validation command:

```powershell
python scripts/validate_schemas.py
```

Expected result:

```text
- all schema files parse
- all valid fixtures pass
- all invalid fixtures fail for expected reasons
- dashboard payload schema validates
```

Schema packaging rules:

```text
- schemas are versioned
- every derived artifact has a schema
- schema changes require migration notes
- dashboard and backend use the same schema source
```

## 11. Fixture Setup

Minimum Gate 0 fixture files:

```text
fixtures/studies/minimal_doe/study.json
fixtures/studies/minimal_doe/factor_space.json
fixtures/studies/minimal_doe/responses.json
fixtures/studies/minimal_doe/dashboard_payload.json
fixtures/studies/invalid_bad_study_id/study.json
fixtures/studies/invalid_bad_factor_bounds/factor_space.json
fixtures/studies/invalid_duplicate_normalized_names/factor_space.json
fixtures/studies/invalid_missing_required_metadata/study.json
fixtures/studies/invalid_units/factor_space.json
fixtures/dashboard/empty_payload_state.json
fixtures/dashboard/phase0_design_only_payload.json
fixtures/dashboard/payload_validation_error.json
```

Required fixture groups:

```text
fixtures/studies/minimal_doe/
fixtures/studies/ivt_launch_no_costs/
fixtures/studies/ivt_launch_with_costs/
fixtures/studies/ivt_timecourse/
fixtures/studies/ivt_rank_deficient_model/
fixtures/studies/ivt_missing_response_values/
fixtures/studies/ivt_invalid_units/
fixtures/studies/ivt_construct_yield/
fixtures/studies/ivt_design_space/
fixtures/studies/ivt_verification/
fixtures/studies/ivt_construct_transfer/
fixtures/studies/ivt_counterion/
```

Each fixture group must include:

```text
- source input files
- expected normalized artifacts
- expected warning or error records
- expected dashboard payload when applicable
- README.md describing fixture purpose and expected behavior
```

Fixture rules:

```text
- use synthetic data
- do not include confidential experimental records
- do not include proprietary prices
- use direct fixture costs only for cost-analysis tests
- include invalid fixtures for validation tests
- invalid fixtures must document the expected error code and JSON path
```

## 11.1 Dependency Lock Setup

The backend lock is required before scientific algorithms are implemented:

```powershell
uv --directory mcp-server lock
uv --directory mcp-server sync --all-extras --dev
uv --directory mcp-server run python -c "import doe_toolchain"
```

The dashboard lock is required before dashboard fixtures are treated as stable:

```powershell
pnpm --dir apps/dashboard install --frozen-lockfile
```

Expected result:

```text
- uv.lock exists.
- apps/dashboard/pnpm-lock.yaml exists.
- backend import/version smoke test records Python and numerical package versions.
- dashboard package install is reproducible from lockfile.
```

## 12. Running Tests

### 12.1 Backend Tests

Command:

```powershell
python -m pytest mcp-server/tests
```

Expected result:

```text
- unit tests pass
- MCP contract tests pass
- schema tests pass when invoked by backend tests
```

### 12.2 Regression Tests

Command:

```powershell
python -m pytest mcp-server/tests --run-regression
```

Expected result:

```text
- golden output comparisons pass within declared tolerances
- fixed-seed DOE and model fixtures remain stable
```

### 12.3 Dashboard Tests

Commands:

```powershell
pnpm --dir apps/dashboard test
pnpm --dir apps/dashboard typecheck
pnpm --dir apps/dashboard build
pnpm --dir apps/dashboard test:e2e
```

Expected result:

```text
- component tests pass
- TypeScript passes
- build succeeds
- browser smoke tests pass for desktop, tablet, and mobile viewports
```

### 12.4 End-to-End Launch Workflow

Command:

```powershell
python scripts/run_launch_workflow.py --fixture fixtures/studies/ivt_launch_no_costs
python scripts/run_launch_workflow.py --fixture fixtures/studies/ivt_launch_with_costs
```

Expected result:

```text
- no-cost workflow completes with economics unavailable
- with-cost workflow completes with cost efficiency calculated
- both workflows produce dashboard_payload.json
- both workflows write audit logs
```

### 12.5 Validation Report

Command:

```powershell
python scripts/run_validation_report.py --scope launch
```

Expected result:

```text
- validation report is written under validation-reports/
- report states whether launch gate passed
- report includes test summaries, fixture hashes, package versions, and dashboard screenshot paths
```

Paper-class validation command:

```powershell
python scripts/run_validation_report.py --scope paper-class
```

Expected result:

```text
- report states whether paper-class gate passed
- report includes design-space, verification comparison, construct-transfer, and counterion scenarios
```

## 13. Local Workflow Smoke Test

After setup, run this smoke test:

```powershell
python scripts/run_launch_workflow.py --fixture fixtures/studies/ivt_launch_no_costs
pnpm --dir apps/dashboard build
pnpm --dir apps/dashboard test:e2e
```

Expected artifacts:

```text
outputs/studies/<study_id>/study.json
outputs/studies/<study_id>/factor_space.json
outputs/studies/<study_id>/responses.json
outputs/studies/<study_id>/designs/<design_id>/design_matrix.csv
outputs/studies/<study_id>/observations/endpoint_observations.csv
outputs/studies/<study_id>/observations/time_resolved_observations.csv
outputs/studies/<study_id>/derived/theoretical_yield.json
outputs/studies/<study_id>/models/<fit_id>/model_fit.json
outputs/studies/<study_id>/derived/effects.json
outputs/studies/<study_id>/derived/recommendations.json
outputs/studies/<study_id>/derived/verification_plan.json
outputs/studies/<study_id>/dashboard_payload.json
outputs/studies/<study_id>/audit_log.jsonl
```

Expected behavior:

```text
- dashboard opens or builds against generated payload
- economics view states that costs were not supplied
- other launch views remain usable
- warnings and unavailable states are visible
```

## 14. Plugin Installation in Codex

Local plugin installation should follow Codex's local plugin mechanism. The plugin package must be structured so Codex can discover:

```text
- plugins/doe-scientific-toolchain/.codex-plugin/plugin.json
- plugins/doe-scientific-toolchain/skills/scientific-study-designer/SKILL.md
- project-scoped MCP config in .codex/config.toml
- optional plugin-bundled .mcp.json after cache-safe command verification
```

After installation, verify:

```text
- Codex lists the DOE Scientific Toolchain plugin
- Codex can read the skill
- Codex can start the MCP server
- Codex can call create_or_update_study
- Codex can generate a dashboard payload through tools
```

Gate 0 Plugin/MCP smoke test:

```text
1. Install or enable the repo-local plugin from .agents/plugins/marketplace.json.
2. Copy .codex/config.toml.example to .codex/config.toml or apply equivalent MCP settings.
3. Start Codex from the repository root.
4. Ask Codex to use scientific-study-designer.
5. Call create_or_update_study with a minimal study request.
6. Confirm outputs/studies/<study_id>/study.json and audit_log.jsonl are written.
7. Confirm the tool response includes study_id, run_id, status, warnings, errors, and artifact_paths.
```

The smoke test fails Gate 0 if Codex cannot discover the plugin, load the skill, start MCP, or call the skeleton tool.

The skill should expose example prompts:

```text
Create an IVT DOE study with Mg:NTP ratio, NTP concentration, DNA template, and T7 RNAP as factors.

Generate a D-optimal design for this study and save the matrix.

Import these endpoint observations and fit response-surface models for yield and dsRNA.

Register this construct and calculate theoretical and relative yield.

Calculate COGS only from this component cost table.

Launch the dashboard preview for this study.
```

## 15. Release Packaging

Release package must include:

```text
- plugin metadata
- skill instructions
- Python MCP server package
- dashboard app
- schemas
- fixtures
- validation scripts
- planning docs
- README
- changelog
- dependency lockfiles
```

Release package must exclude:

```text
- user study outputs
- validation reports from private datasets
- local virtual environments
- package manager caches
- secrets
- private cost tables
- proprietary experimental data
```

Recommended ignore entries:

```text
.venv/
node_modules/
outputs/studies/*
validation-reports/*
.pytest_cache/
apps/dashboard/test-results/
apps/dashboard/playwright-report/
*.log
.env
.env.*
```

Keep empty output directories with safe marker files when needed:

```text
outputs/studies/.gitkeep
validation-reports/.gitkeep
```

## 16. Versioning

Versioning policy:

```text
- plugin package uses semantic versioning
- MCP API has its own api_version
- schemas have schema_version
- scientific methods have method_version
- dashboard payload has payload_version
```

Version changes:

```text
- patch version for bug fixes that do not change scientific outputs
- minor version for additive tools, schemas, or dashboard views
- major version for breaking API, schema, or artifact changes
- method version change for scientific behavior changes
```

Release notes must state:

```text
- plugin version
- MCP API version
- schema versions changed
- method versions changed
- validation gate status
- known limitations
```

## 17. Troubleshooting

### 17.1 MCP Server Does Not Start

Check:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip show doe-toolchain
python -m doe_toolchain.server
```

Common causes:

```text
- virtual environment not activated
- package not installed in editable mode
- missing dependency
- wrong working directory in plugin metadata
- import path mismatch
```

### 17.2 Schema Validation Fails

Check:

```powershell
python scripts/validate_schemas.py
```

Common causes:

```text
- schema_version missing
- method_version missing on derived artifact
- unit missing from scientific quantity
- payload field renamed without dashboard update
- fixture expected output out of sync with method version
```

### 17.3 Cost Analysis Is Unavailable

Expected when:

```text
- user did not provide direct component costs
- cost table is incomplete under complete-cost policy
- component usage table is missing
```

Resolution:

```text
- provide a direct component cost table
- provide component usage mapping
- use the no-cost workflow when economics is not required
```

The toolchain should continue to run DOE, modeling, effects, recommendations, verification planning, and dashboard preview without cost inputs.

### 17.4 Dashboard Loads but Shows Incompatible Payload

Check:

```text
- dashboard_payload.json exists
- payload_version is supported by the dashboard
- payload was generated by the current backend
- schema validation passes
```

Resolution:

```powershell
python scripts/run_launch_workflow.py --fixture fixtures/studies/ivt_launch_no_costs
pnpm --dir apps/dashboard build
```

### 17.5 Browser Smoke Tests Fail

Check:

```powershell
pnpm --dir apps/dashboard exec playwright install
pnpm --dir apps/dashboard test:e2e
```

Common causes:

```text
- dashboard dev server not started by test harness
- missing Playwright browser
- payload fixture path changed
- console error from incompatible payload
- viewport layout regression
```

### 17.6 Fixed-Seed Regression Changed

Check:

```powershell
python -m pytest mcp-server/tests --run-regression
```

Resolution rules:

```text
- if behavior changed intentionally, update method_version and golden outputs
- if behavior changed unintentionally, fix the implementation
- record golden-output diffs in validation report
```

## 18. Clean Workspace Commands

Clean generated study outputs:

```powershell
Remove-Item -LiteralPath .\outputs\studies\* -Recurse -Force
```

Clean dashboard test outputs:

```powershell
Remove-Item -LiteralPath .\apps\dashboard\test-results -Recurse -Force
Remove-Item -LiteralPath .\apps\dashboard\playwright-report -Recurse -Force
```

Clean validation reports:

```powershell
Remove-Item -LiteralPath .\validation-reports\* -Recurse -Force
```

Safety rule:

```text
Run cleanup commands only from the repository root and only against generated output directories.
```

## 19. Developer Quality Checklist

Before opening a release candidate:

```text
- Python package installs from clean virtual environment.
- Dashboard package installs from lockfile.
- MCP server starts.
- Plugin metadata validates.
- Schemas validate.
- Backend tests pass.
- Regression tests pass.
- Dashboard tests pass.
- End-to-end no-cost workflow passes.
- End-to-end direct-cost workflow passes.
- Validation report is generated.
- No generated private outputs are included in release package.
```

## 20. User-Facing Setup Checklist

A user should be able to:

```text
1. Install or enable the plugin in Codex.
2. Ask Codex to create a DOE study.
3. Ask Codex to generate a DOE matrix.
4. Provide observation data.
5. Provide construct sequence if relative yield is needed.
6. Provide direct component costs if economics is needed.
7. Ask Codex to fit models and analyze effects.
8. Ask Codex to generate recommendations or verification runs.
9. Ask Codex to launch the dashboard preview.
10. Review warnings, assumptions, and unavailable states.
```

The user should not need to:

```text
- edit generated JSON manually for normal workflows
- install hosted services
- provide reagent costs when economics is not needed
- provide API keys
- upload data to a cloud service
```

## 21. Final Packaging Rule

The package is ready only when a clean local setup can install the Python backend, install the dashboard, validate schemas, run launch workflows with and without direct component costs, generate a dashboard payload, and produce a validation report without relying on external services or undocumented manual steps.
