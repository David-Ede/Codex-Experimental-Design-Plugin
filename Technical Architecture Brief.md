# Technical architecture brief: Codex scientific toolchain plugin with live React visualization

## 1. Executive conclusion

**Is this possible inside Codex today?**
Yes, with one important boundary: the **toolchain orchestration** is a natural fit for **Codex plugin + skills + MCP server**, and the **live visualization surface** should be a normal local or hosted web app previewed in the **Codex in-app browser**. Codex plugins are documented as installable bundles that can include skills, app integrations, MCP server configuration, and assets; Codex also documents local dev-server previews in the in-app browser. ([OpenAI Developers][1])

**What exactly is possible?**

The realistic product is:

```text
Codex plugin
  ├─ skills that teach Codex the DOE / modeling / optimization workflow
  ├─ MCP configuration that exposes a Python scientific toolchain server
  └─ install metadata / assets

Python MCP server
  ├─ DOE engine
  ├─ statistics / response-surface modeling engine
  ├─ next-experiment optimization engine
  ├─ process economics / COGS engine
  └─ dashboard payload + preview-launch tools

React dashboard app
  ├─ local Vite/React dev server, or static/file-backed build
  ├─ reads typed dashboard payloads emitted by MCP tools
  └─ is reviewed in the Codex in-app browser
```

Codex can then work in the normal agent loop: read files, call tools, edit or generate the React app, run commands, and verify outputs. OpenAI documents that Codex works by repeatedly calling the model and taking actions such as file reads, file edits, and tool calls until the task completes or is canceled. ([OpenAI Developers][2])

**What is not clearly supported?**

A **native custom embedded UI surface inside a Codex plugin** is **not documented**. The docs document Codex plugin components as skills, apps/connectors, MCP servers, and assets, but they do not document a plugin API for embedding an arbitrary React iframe/widget directly inside Codex. By contrast, OpenAI documents optional React/plain web components inside **ChatGPT apps** as ChatGPT iframe widgets, which is a different surface. ([OpenAI Developers][1])

Also, a programmatic “open this URL in the Codex in-app browser” API for plugins/MCP tools is **not clearly documented**. The documented browser path is: start a dev server, open an unauthenticated local route by clicking a URL, toolbar, manual navigation, or keyboard shortcut, then review and comment. ([OpenAI Developers][3])

**Recommended implementation pattern**

Build **plugin + Python MCP + local/web React app opened in the Codex in-app browser**.

Do **not** try to build a native Codex plugin UI. Treat the dashboard as a standard web app:

```text
User prompt
  → Codex skill instructions
  → MCP tool calls
  → JSON dashboard payload
  → React app renders payload
  → Codex/user opens localhost URL in in-app browser
  → user comments / asks for changes
  → Codex updates payload, app code, or both
```

This pattern is the most buildable, documented, and native-feeling today.

---

## 2. Evidence-backed capability map

| Capability                                    |                                                           Status | Evidence                                                                                                                                                                                                                                        | Practical implication                                                                                                                                       |
| --------------------------------------------- | ---------------------------------------------------------------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Plugin manifests**                          |                                                    **Supported** | Codex plugin docs state every plugin has `.codex-plugin/plugin.json`; documented manifest fields include `name`, `version`, `description`, `skills`, `mcpServers`, `apps`, and `interface`. ([OpenAI Developers][4])                            | Use `plugin.json` as the installable package entry point. Keep it thin and documented.                                                                      |
| **Bundled skills**                            |                                                    **Supported** | Skills are reusable workflow instructions; a skill is a directory with `SKILL.md` and optional scripts/references/assets. Plugins can include one or more skills. ([OpenAI Developers][5])                                                      | Put scientific workflow behavior in skills, not in the manifest.                                                                                            |
| **Skill metadata and MCP dependencies**       |                                                    **Supported** | `agents/openai.yaml` can configure UI metadata, invocation policy, and tool dependencies; the docs show `dependencies.tools` entries of type `mcp`. ([OpenAI Developers][5])                                                                    | Declare the scientific MCP dependency in the skill metadata so Codex knows the workflow expects that server.                                                |
| **Bundled MCP config in plugin**              |                       **Supported, but schema details are thin** | Plugin docs say a plugin can include `.mcp.json` and a manifest `mcpServers` pointer. The full public build page does not show a `.mcp.json` schema example. ([OpenAI Developers][4])                                                           | Use plugin-bundled MCP for distribution, but keep a documented `.codex/config.toml` fallback for MVP. Use `$plugin-creator` to scaffold the current format. |
| **Codex MCP support**                         |                                                    **Supported** | Codex app, CLI, and IDE Extension share MCP settings; Codex supports stdio and streamable HTTP MCP servers, with documented `command`, `args`, `env`, `cwd`, `url`, timeouts, allow/deny tool lists, and auth options. ([OpenAI Developers][6]) | Implement the scientific toolchain as a local stdio Python MCP server first.                                                                                |
| **MCP tools with schemas**                    |                                        **Supported by MCP spec** | MCP tools have names, descriptions, `inputSchema`, optional `outputSchema`, and can return structured content; tools are discovered via `tools/list` and invoked via `tools/call`. ([Model Context Protocol][7])                                | Define stable JSON schemas for DOE, models, optimization, economics, and dashboard payloads.                                                                |
| **Python MCP server implementation**          |                                 **Supported via MCP Python SDK** | The MCP docs show Python setup with `mcp[cli]` and `FastMCP`; `FastMCP` uses Python type hints and docstrings to generate tool definitions. ([Model Context Protocol][8])                                                                       | Use `FastMCP` for a solo-builder MVP.                                                                                                                       |
| **In-app browser previews**                   |                                                    **Supported** | Codex documents the in-app browser for shared rendered web-page review inside a thread. It supports local dev servers, file-backed previews, and public pages that do not require sign-in. ([OpenAI Developers][3])                             | The React dashboard should be unauthenticated during local preview and reachable on localhost.                                                              |
| **Live local dev server previews**            |                                                    **Supported** | Codex docs instruct users to start a development server in the integrated terminal or via a local environment action, then open the route in the in-app browser. ([OpenAI Developers][3])                                                       | Add a “Run dashboard” local environment action and/or MCP `launch_dashboard_preview` helper.                                                                |
| **App integrations / connectors**             |                     **Supported, but not the same as custom UI** | Plugins can include app/connector mappings; Codex app-server docs describe apps/connectors listed with `app/list` and invoked via `$<app-slug>` / `app://<id>`. ([OpenAI Developers][1])                                                        | Do not confuse Codex “apps/connectors” with a custom embedded dashboard surface.                                                                            |
| **Native custom embedded UI in Codex plugin** |                                               **Not documented** | The plugin docs list skills, apps/connectors, MCP config, and assets; the in-app browser docs describe previewing web pages. A separate ChatGPT Apps flow documents iframe widgets for ChatGPT, not Codex plugins. ([OpenAI Developers][4])     | Build the dashboard as a web app and open it in the in-app browser.                                                                                         |
| **Workflow automation**                       | **Supported for recurring/background use, not required for MVP** | Codex automations can use plugins and skills; thread automations can wake up the same thread on a schedule. ([OpenAI Developers][9])                                                                                                            | Useful later for long-running campaigns, model refits, or nightly DOE status checks.                                                                        |
| **Multi-step Codex orchestration**            |                                                    **Supported** | Codex handles prompts as threads with tool calls, file edits, and command runs; subagents are available by explicit request for parallel workflows. ([OpenAI Developers][2])                                                                    | A single Codex thread can orchestrate DOE design, fitting, dashboard updates, and review. Use subagents only later.                                         |
| **Self-serve public plugin publishing**       |                    **Not yet generally documented as available** | Build docs say adding plugins to the official Plugin Directory and self-serve plugin publishing/management are “coming soon.” ([OpenAI Developers][4])                                                                                          | For MVP, distribute through a local repo or personal marketplace.                                                                                           |

---

## 3. Full system architecture

### Recommended architecture

```text
┌────────────────────────────────────────────────────────────────────┐
│ User                                                               │
│ "Design a screening DOE for 6 factors and show the dashboard."     │
└───────────────┬────────────────────────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────────────────────────┐
│ Codex thread                                                       │
│ - Selects scientific-study skill                                   │
│ - Reads repo docs / uploaded CSVs                                  │
│ - Calls MCP tools                                                  │
│ - Edits React app or dashboard payload files                       │
│ - Runs tests / preview server                                      │
└───────────────┬────────────────────────────────────────────────────┘
                │ skill instructions + MCP tool calls
                ▼
┌────────────────────────────────────────────────────────────────────┐
│ Codex plugin                                                       │
│ .codex-plugin/plugin.json                                          │
│ skills/scientific-study-designer/SKILL.md                          │
│ skills/.../agents/openai.yaml                                      │
│ .mcp.json, if using plugin-bundled MCP config                      │
│ assets/                                                           │
└───────────────┬────────────────────────────────────────────────────┘
                │ MCP transport: stdio first; HTTP later
                ▼
┌────────────────────────────────────────────────────────────────────┐
│ Python MCP server: doe-scientific-toolchain                        │
│                                                                    │
│ Tools:                                                             │
│ - validate_factor_space                                            │
│ - design_doe                                                       │
│ - fit_response_surface                                             │
│ - analyze_effects                                                  │
│ - suggest_next_experiment                                          │
│ - calculate_cogs_impact                                            │
│ - generate_dashboard_payload                                       │
│ - launch_dashboard_preview                                         │
│                                                                    │
│ Modules:                                                           │
│ - doe/                                                             │
│ - stats/                                                           │
│ - optimize/                                                        │
│ - economics/                                                       │
│ - dashboard_payload/                                               │
│ - persistence/                                                     │
└───────────────┬────────────────────────────────────────────────────┘
                │ writes typed artifacts
                ▼
┌────────────────────────────────────────────────────────────────────┐
│ Workspace outputs                                                  │
│ outputs/studies/<study_id>/                                        │
│ - factor_space.json                                                │
│ - design_matrix.csv                                                │
│ - model_fit.json                                                   │
│ - effects.json                                                     │
│ - next_experiments.json                                            │
│ - cogs.json                                                        │
│ - dashboard_payload.json                                           │
│ - audit_log.jsonl                                                  │
└───────────────┬────────────────────────────────────────────────────┘
                │ read by app over local file/dev endpoint
                ▼
┌────────────────────────────────────────────────────────────────────┐
│ React visualization app                                            │
│ apps/dashboard                                                     │
│ - Experiment matrix                                                │
│ - Factor-response plots                                            │
│ - Pareto charts                                                    │
│ - Contour maps                                                     │
│ - COGS overlays                                                    │
│ - Scenario comparison views                                        │
└───────────────┬────────────────────────────────────────────────────┘
                │ localhost URL / file-backed preview
                ▼
┌────────────────────────────────────────────────────────────────────┐
│ Codex in-app browser                                               │
│ - Opens unauthenticated local route                                │
│ - User reviews and comments                                        │
│ - Codex updates code/payload and refreshes                         │
└────────────────────────────────────────────────────────────────────┘
```

### Deployment shape

**MVP deployment**

```text
repo checkout
  ├─ plugin installed through repo-local marketplace
  ├─ Python MCP server launched by stdio
  ├─ React dashboard launched by Vite on localhost
  └─ dashboard payloads stored under outputs/studies/
```

**Team/internal deployment**

```text
repo or internal package
  ├─ plugin distributed through personal/team marketplace
  ├─ MCP server still local stdio, or internal streamable HTTP
  ├─ dashboard local dev server for authoring
  └─ optional hosted read-only dashboard for study review
```

**Production deployment**

```text
internal platform
  ├─ Codex plugin for workflow entry points
  ├─ authenticated MCP HTTP server for validated scientific engines
  ├─ signed / access-controlled study artifact store
  ├─ hosted dashboard with audit trail
  └─ Codex remains authoring/orchestration layer, not source of scientific truth
```

---

## 4. Component-by-component breakdown

### 4.1 Plugin manifest

**Purpose**
Identifies the plugin and points Codex to bundled skills, MCP config, and optional app/connector mappings.

**Internal structure**

```text
.codex-plugin/plugin.json
assets/
skills/
.mcp.json             # optional; schema details should be verified with plugin creator
.app.json             # optional; not needed for MVP unless using Codex app/connectors
```

**Inputs / outputs**

Input: installed plugin package.
Output: Codex-visible skills, install metadata, optional MCP/app wiring.

**Failure modes**

* Manifest path wrong.
* Paths not relative to plugin root.
* Plugin installed from cache but source files changed; restart/reinstall needed.
* `.mcp.json` format mismatch because public docs document the file’s existence but not a full schema.

**Observability**

* Codex plugin directory shows install status.
* Codex config records enabled/disabled plugin state.
* Skill picker should show bundled skills.
* MCP settings should show server if wiring succeeded.

**MVP scope**

Use one plugin with one primary skill and one optional helper skill. Keep the manifest documented and minimal.

---

### 4.2 Skill files

**Purpose**
Teach Codex the domain workflow: when to validate factor space, call DOE tools, fit models, update payloads, and open a browser preview.

**Internal structure**

```text
skills/scientific-study-designer/
  SKILL.md
  agents/openai.yaml
  references/
    doe-principles.md
    response-surface-checklist.md
    scientific-validation.md
  scripts/
    validate_dashboard_payload.py
```

**Inputs / outputs**

Input: user prompt, factor definitions, uploaded datasets, repo files, previous study artifacts.
Output: tool-call plan, MCP calls, code/payload changes, user-facing explanation.

**Failure modes**

* Skill implicitly invoked when it should not be.
* Codex explains science without calling deterministic tools.
* Skill instructions become too long and dilute context.
* MCP dependency missing.

**Observability**

* Codex thread shows skill invocation.
* MCP calls visible in thread/tool trace.
* `outputs/studies/<study_id>/audit_log.jsonl` records deterministic steps.

**MVP scope**

One focused `scientific-study-designer` skill. Do not split into many skills until the workflow stabilizes.

---

### 4.3 MCP config

**Purpose**
Connect Codex to the Python scientific server.

**Recommended development config path**

Use project-scoped Codex MCP config in `.codex/config.toml` during development because the TOML server fields are documented and the paths resolve from the repository root. Codex documents stdio `command`, `args`, `env`, `env_vars`, `cwd`, streamable HTTP `url`, and timeout/tool allowlist options. ([OpenAI Developers][10])

**Plugin-bundled config**

Use plugin `.mcp.json` after scaffolding with `$plugin-creator` and after proving the command is cache-safe. Plugin docs document that the manifest can point to `.mcp.json`, but the public page does not show the exact schema. ([OpenAI Developers][4])

**Failure modes**

* Server startup timeout.
* Python environment missing.
* Relative paths resolve differently from expected plugin cache location.
* Tool timeout too short for model fitting or optimization.
* Network disabled if using HTTP server.

**Observability**

* MCP server stderr logs.
* Codex MCP settings.
* Tool call failures in Codex thread.
* Per-tool structured error payloads.

**MVP scope**

Local stdio server with a clear `cwd` and an absolute repo path in config during development.

---

### 4.4 Python MCP server

**Purpose**
Be the deterministic scientific backend. Codex should ask it to compute, validate, fit, optimize, and produce typed dashboard payloads.

**Internal structure**

```text
mcp-server/src/doe_toolchain/
  server.py
  tools/
    doe_tools.py
    model_tools.py
    optimization_tools.py
    economics_tools.py
    dashboard_tools.py
  engines/
    doe/
    stats/
    optimization/
    economics/
  schemas/
  persistence/
  observability/
```

**Inputs / outputs**

Inputs:

* factor definitions
* response definitions
* constraints
* experimental data
* model choices
* economics assumptions
* study IDs

Outputs:

* validated factor spaces
* DOE matrices
* fitted model summaries
* effect estimates
* next-experiment recommendations
* COGS impacts
* dashboard payload JSON
* audit logs

**Failure modes**

* Invalid factor bounds or categorical levels.
* Aliased or underpowered design.
* Missing response data.
* Singular/ill-conditioned model matrix.
* Extrapolation beyond factor space.
* Optimizer suggests infeasible experiments.
* Economics assumptions incomplete.
* Dashboard payload schema mismatch.

**Observability**

* Structured logs per tool call.
* `study_id`, `run_id`, and `artifact_hash`.
* Audit log with input hash, output hash, engine version, package versions.
* Deterministic random seed captured in every stochastic design/optimization result.
* Tool-level warnings returned in structured content.

**MVP scope**

Start with:

* fractional factorial / Plackett-Burman / Latin hypercube screening
* OLS response-surface fitting
* standardized effects and Pareto chart payload
* simple desirability-based next-experiment suggestions
* basic COGS calculator
* static dashboard payload generation

---

### 4.5 DOE / statistics / economics modules

**DOE engine**

Purpose:

* Build screening and response-surface designs.
* Enforce bounds, levels, forbidden combinations, replicates, blocks, randomization, and seeds.

MVP:

* full factorial for small spaces
* fractional factorial for 2-level screening
* Latin hypercube for mixed continuous spaces
* central composite or Box-Behnken once response-surface work begins

Failure modes:

* design too large
* categorical/continuous encoding mismatch
* confounded effects not disclosed
* constraints make design infeasible

**Statistics / model fitting engine**

Purpose:

* Fit response models.
* Estimate main effects, interactions, curvature, uncertainty.
* Generate factor-response and contour payloads.

MVP:

* OLS / GLM-style response surface
* robust validation metrics
* coefficient table
* standardized effects
* residual diagnostics
* prediction grid for visualization

Failure modes:

* singular design matrix
* too many terms for rows
* unmodeled batch/block effects
* invalid inference due to non-normal or heteroscedastic residuals

**Optimization / next-experiment engine**

Purpose:

* Recommend next experiments given response goals and constraints.

MVP:

* desirability score
* candidate-grid search
* D-optimal augment heuristic
* simple uncertainty/exploration bonus

Failure modes:

* all candidates infeasible
* optimizer exploits model extrapolation
* duplicate experiment suggestions
* ignores operational constraints

**Process economics / COGS engine**

Purpose:

* Translate factor settings and predicted responses into cost, yield, throughput, and scenario tradeoffs.
* Treat economics as optional: the plugin must run without cost inputs, but should model cost efficiency when the user supplies direct component costs.

MVP:

* component-cost input schema
* reagent cost per condition
* yield/titer/productivity basis
* cost efficiency, such as product mass per unit currency
* optional price ranges / sensitivity
* clear "economics unavailable" warnings when costs are omitted

Launch behavior:

```text
- COGS/cost-efficiency scaffolding ships at launch.
- DOE, model fitting, and dashboard generation do not require cost inputs.
- If the user provides component costs, the MCP server calculates cost by condition.
- If costs are missing, the tool skips economics rather than inventing prices.
- Cost claims must cite the user-provided cost table and units.
```

Failure modes:

* missing units
* inconsistent basis, such as per-batch vs per-kg
* hidden assumptions in overhead multipliers
* inferred or stale reagent prices presented as facts
* false precision in early-stage economics

---

### 4.6 React app

**Purpose**
Render the scientific state in a reviewable, interactive surface.

**Internal structure**

```text
apps/dashboard/src/
  main.tsx
  app/
    routes.tsx
    StudyDashboard.tsx
  data/
    dashboardPayload.schema.ts
    useDashboardPayload.ts
  components/
    ExperimentMatrix/
    FactorResponse/
    ParetoChart/
    ContourMap/
    CogsOverlay/
    ScenarioCompare/
    NextExperiments/
    Diagnostics/
  lib/
    format.ts
    units.ts
    transforms.ts
```

**Inputs / outputs**

Input:

* `DashboardPayload` JSON produced by MCP server.

Output:

* Browser-rendered dashboard.
* Optional user annotations via Codex browser comments.
* Optional exported PNG/CSV/HTML artifacts.

**Failure modes**

* Payload schema mismatch.
* Charts silently misread encoded categorical factors.
* Large payload causes slow rendering.
* Polling stale payload.
* Browser route requires auth, which Codex in-app browser does not support.

**Observability**

* Payload version displayed in footer.
* Study ID / run ID / generated timestamp visible.
* Client-side schema validation errors rendered in a diagnostics panel.
* Dev console warnings for missing chart fields.
* Visual regression screenshots later.

**MVP scope**

One route:

```text
/studies/:studyId
```

One payload file:

```text
outputs/studies/<study_id>/dashboard_payload.json
```

One dev command:

```bash
pnpm --dir apps/dashboard dev --host 127.0.0.1 --port 5173
```

---

### 4.7 Browser preview workflow

**Purpose**
Make the dashboard feel native to Codex without relying on undocumented embedded UI.

**Workflow**

```text
1. MCP tool writes/updates dashboard payload.
2. Codex starts or confirms dashboard dev server.
3. MCP tool returns localhost URL.
4. Codex displays the URL in the thread.
5. User opens it in the in-app browser by clicking or manual navigation.
6. User leaves browser comments or asks follow-up changes.
7. Codex updates data payload, app code, or both.
```

The Codex in-app browser is explicitly intended for local development servers, file-backed previews, and public pages that do not require sign-in; it does not support auth flows, existing cookies, browser extensions, or normal browser profile state. ([OpenAI Developers][3])

---

## 5. Suggested repository / file structure

```text
scientific-codex-toolchain/
  README.md
  AGENTS.md
  pyproject.toml
  package.json
  pnpm-workspace.yaml
  .gitignore
  .env.example

  .codex/
    config.toml.example          # documented fallback MCP config
    local-environment.md         # setup/actions instructions

  .agents/
    plugins/
      marketplace.json           # repo-local marketplace for MVP testing

  plugins/
    doe-scientific-toolchain/
      .codex-plugin/
        plugin.json
      .mcp.json                  # plugin-bundled MCP config; verify generated format
      skills/
        scientific-study-designer/
          SKILL.md
          agents/
            openai.yaml
          references/
            doe-principles.md
            model-fitting-checklist.md
            economics-assumptions.md
            ivt-qbd-study-template.md
          scripts/
            validate_dashboard_payload.py
      assets/
        icon.png
        logo.png
        screenshot-dashboard.png

  mcp-server/
    pyproject.toml
    README.md
    src/
      doe_toolchain/
        __init__.py
        server.py

          tools/
            __init__.py
            doe_tools.py
            model_tools.py
            optimization_tools.py
            economics_tools.py
            dashboard_tools.py
            ivt_tools.py

        engines/
          doe/
            __init__.py
            factor_space.py
            screening.py
            optimal_design.py
            response_surface.py
            randomization.py
          stats/
            __init__.py
            fit.py
            effects.py
            diagnostics.py
            prediction_grid.py
            time_resolved.py
            design_space_probability.py
          optimization/
            __init__.py
            desirability.py
            candidate_generation.py
            next_experiment.py
            verification_plan.py
          economics/
            __init__.py
            cogs.py
            sensitivity.py
            scenarios.py
          ivt/
            __init__.py
            sequence.py
            theoretical_yield.py
            construct_transfer.py
            counterion.py

        schemas/
          factor_space.schema.json
          doe_design.schema.json
          model_fit.schema.json
          time_resolved_observations.schema.json
          sequence.schema.json
          economics.schema.json
          dashboard_payload.schema.json

        persistence/
          artifacts.py
          study_store.py

        observability/
          logging.py
          audit.py

    tests/
      test_factor_space.py
      test_design_doe.py
      test_optimal_design.py
      test_model_fit.py
      test_theoretical_yield.py
      test_cogs.py
      test_design_space_probability.py
      test_dashboard_payload_schema.py

  apps/
    dashboard/
      package.json
      vite.config.ts
      tsconfig.json
      index.html
      src/
        main.tsx
        app/
          StudyDashboard.tsx
          routes.tsx
        data/
          dashboardPayload.schema.ts
          useDashboardPayload.ts
        components/
          ExperimentMatrix/
          FactorResponse/
          ParetoChart/
          ContourMap/
          CogsOverlay/
          ScenarioCompare/
          NextExperiments/
          Diagnostics/
        test/
          payloadFixtures.ts

  shared/
    schemas/
      dashboard_payload.schema.json
      factor_space.schema.json
      tool_outputs.schema.json
    examples/
      screening_6_factor_request.json
      fitted_response_surface_payload.json

  examples/
    screening_6_factors/
      request.json
      observed_data.csv
      expected_dashboard_payload.json

  outputs/
    .gitkeep
    studies/
      .gitkeep

  logs/
    .gitkeep
```

---

## 6. Example plugin architecture artifacts

### 6.1 Documented manifest example

This uses fields shown in the official plugin manifest examples: `name`, `version`, `description`, `skills`, `mcpServers`, `apps`, and `interface`. ([OpenAI Developers][4])

```json
{
  "name": "doe-scientific-toolchain",
  "version": "0.1.0",
  "description": "DOE, response-surface modeling, optimization, process economics, and dashboard workflows for Codex.",
  "author": {
    "name": "Your Team",
    "email": "team@example.com",
    "url": "https://example.com"
  },
  "homepage": "https://example.com/doe-scientific-toolchain",
  "repository": "https://example.com/repo/doe-scientific-toolchain",
  "license": "Proprietary",
  "keywords": ["doe", "statistics", "optimization", "process-economics", "dashboard"],
  "skills": "./skills/",
  "mcpServers": "./.mcp.json",
  "interface": {
    "displayName": "Scientific Toolchain",
    "shortDescription": "Design studies, fit models, optimize experiments, and preview dashboards.",
    "longDescription": "A Codex workflow bundle for scientific DOE, response-surface modeling, next-experiment selection, COGS analysis, and live dashboard review.",
    "developerName": "Your Team",
    "category": "Data",
    "capabilities": ["Read", "Write"],
    "defaultPrompt": [
      "Use Scientific Toolchain to design a screening DOE.",
      "Use Scientific Toolchain to fit the uploaded experimental data and refresh the dashboard."
    ],
    "brandColor": "#10A37F",
    "composerIcon": "./assets/icon.png",
    "logo": "./assets/logo.png",
    "screenshots": ["./assets/screenshot-dashboard.png"]
  }
}
```

### 6.2 Skill definition

```markdown
---
name: scientific-study-designer
description: Design, analyze, optimize, and visualize scientific DOE studies using the Scientific Toolchain MCP server and React dashboard.
---

Use this skill when the user asks Codex to design a study, fit experimental data, analyze factor effects, optimize next experiments, evaluate COGS, or refresh a scientific dashboard.

Workflow rules:

1. Do not invent DOE matrices, coefficients, p-values, COGS estimates, reagent prices, or next-experiment recommendations.
2. Use the doe-scientific-toolchain MCP server for deterministic calculations.
3. Start by validating the factor space and response definitions.
4. Persist every study artifact under `outputs/studies/<study_id>/`.
5. Generate or update `dashboard_payload.json` after every material analytical change.
6. When a visual review is requested, start or use the dashboard dev server and provide the local preview URL.
7. Explain statistical limitations, aliasing, uncertainty, extrapolation, and economics assumptions in plain language.
8. Run COGS/cost-efficiency analysis only when the user supplies direct component costs or an explicit cost table. If costs are absent, continue without economics and say why.
9. Prefer small, reviewable changes to dashboard code. Do not rewrite chart components unless the requested view requires it.

Canonical MCP sequence for a new DOE:

- `validate_factor_space`
- `design_doe`
- `generate_dashboard_payload`
- `launch_dashboard_preview`

Canonical MCP sequence for uploaded data:

- `validate_factor_space`
- `fit_response_surface`
- `analyze_effects`
- `calculate_cogs_impact`, if economics inputs exist
- `generate_dashboard_payload`
- `launch_dashboard_preview`
```

### 6.3 Skill metadata with MCP dependency

The `agents/openai.yaml` pattern is documented for skill UI metadata, invocation policy, and dependencies. ([OpenAI Developers][5])

```yaml
interface:
  display_name: "Scientific Study Designer"
  short_description: "DOE, model fitting, optimization, COGS, and dashboards"
  icon_small: "./assets/icon.png"
  icon_large: "./assets/logo.png"
  brand_color: "#10A37F"
  default_prompt: "Use Scientific Study Designer to design a DOE and open the dashboard."

policy:
  allow_implicit_invocation: true

dependencies:
  tools:
    - type: "mcp"
      value: "doe-scientific-toolchain"
      description: "Local Python MCP server for DOE, response-surface modeling, next-experiment optimization, COGS, and dashboard payload generation."
      transport: "stdio"
```

### 6.4 Documented fallback MCP config: `.codex/config.toml`

This is the config form I would use during MVP development because Codex documents these fields directly. ([OpenAI Developers][10])

```toml
[mcp_servers.doe-scientific-toolchain]
command = "uv"
args = ["--directory", "mcp-server", "run", "python", "-m", "doe_toolchain.server"]
cwd = "/absolute/path/to/doe-scientific-toolchain-repo"
startup_timeout_sec = 20
tool_timeout_sec = 180
enabled = true
required = true

[mcp_servers.doe-scientific-toolchain.env]
DOE_TOOLCHAIN_OUTPUT_DIR = "outputs/studies"
DOE_TOOLCHAIN_DASHBOARD_APP_DIR = "apps/dashboard"
DOE_TOOLCHAIN_DASHBOARD_PORT = "5173"
DOE_TOOLCHAIN_LOG_LEVEL = "INFO"
```

### 6.5 Illustrative plugin `.mcp.json`

**Status: likely supported but exact schema is not fully shown on the official plugin build page.** The docs say a plugin can include `.mcp.json` and a manifest `mcpServers` pointer; they do not provide a complete public `.mcp.json` schema in the plugin page. Use `$plugin-creator` to generate the current canonical shape before relying on this in distribution. ([OpenAI Developers][4])

```json
{
  "mcpServers": {
    "doe-scientific-toolchain": {
      "command": "uv",
      "args": [
        "--directory",
        "<verified-cache-safe-mcp-server-path>",
        "run",
        "python",
        "-m",
        "doe_toolchain.server"
      ],
      "env": {
        "DOE_TOOLCHAIN_OUTPUT_DIR": "outputs/studies",
        "DOE_TOOLCHAIN_DASHBOARD_APP_DIR": "apps/dashboard",
        "DOE_TOOLCHAIN_DASHBOARD_PORT": "5173"
      }
    }
  }
}
```

Use `.codex/config.toml` for development until this command has been tested from the installed plugin cache.

### 6.6 Environment file

```bash
# .env.example

DOE_TOOLCHAIN_OUTPUT_DIR=outputs/studies
DOE_TOOLCHAIN_DASHBOARD_APP_DIR=apps/dashboard
DOE_TOOLCHAIN_DASHBOARD_HOST=127.0.0.1
DOE_TOOLCHAIN_DASHBOARD_PORT=5173
DOE_TOOLCHAIN_LOG_LEVEL=INFO

# Optional: lock deterministic design generation
DOE_TOOLCHAIN_DEFAULT_RANDOM_SEED=1729

# Optional: forbid remote network calls in scientific tools
DOE_TOOLCHAIN_OFFLINE_MODE=true
```

---

## 7. Example MCP tool definitions

MCP tools should be small, typed, and auditable. The MCP spec supports schema-defined tool inputs, optional output schemas, structured results, and tool execution errors. ([Model Context Protocol][7])

### Shared schema fragments

```json
{
  "FactorSpec": {
    "type": "object",
    "required": ["name", "kind"],
    "properties": {
      "name": { "type": "string" },
      "kind": { "enum": ["continuous", "categorical", "ordinal", "mixture"] },
      "units": { "type": "string" },
      "low": { "type": "number" },
      "high": { "type": "number" },
      "levels": { "type": "array", "items": { "type": ["string", "number"] } },
      "fixed": { "type": "boolean" },
      "transform": { "enum": ["none", "log", "sqrt", "center_scale"] }
    }
  },
  "ResponseSpec": {
    "type": "object",
    "required": ["name", "goal"],
    "properties": {
      "name": { "type": "string" },
      "goal": { "enum": ["maximize", "minimize", "target", "range"] },
      "target": { "type": "number" },
      "lower": { "type": "number" },
      "upper": { "type": "number" },
      "weight": { "type": "number", "default": 1 },
      "units": { "type": "string" }
    }
  }
}
```

### Tool: `validate_factor_space`

**Purpose**
Validate factor names, bounds, levels, units, constraints, and response definitions before any DOE or model fit.

**Input schema**

```json
{
  "type": "object",
  "required": ["factors", "responses"],
  "properties": {
    "study_id": { "type": "string" },
    "factors": { "type": "array", "items": { "$ref": "#/FactorSpec" } },
    "responses": { "type": "array", "items": { "$ref": "#/ResponseSpec" } },
    "constraints": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["expression"],
        "properties": {
          "expression": { "type": "string" },
          "description": { "type": "string" }
        }
      }
    }
  }
}
```

**Output schema**

```json
{
  "type": "object",
  "required": ["study_id", "valid", "normalized_factor_space", "warnings"],
  "properties": {
    "study_id": { "type": "string" },
    "valid": { "type": "boolean" },
    "normalized_factor_space": { "type": "object" },
    "warnings": { "type": "array", "items": { "type": "string" } },
    "errors": { "type": "array", "items": { "type": "string" } },
    "artifact_paths": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Side effects**
Writes `factor_space.json` and audit log.

**Codex usage**
Always call first. If invalid, Codex should ask for missing bounds/units or propose safe defaults explicitly labeled as assumptions.

---

### Tool: `design_doe`

**Purpose**
Generate a DOE matrix.

**Input schema**

```json
{
  "type": "object",
  "required": ["study_id", "design_type"],
  "properties": {
    "study_id": { "type": "string" },
    "design_type": {
      "enum": [
        "full_factorial",
        "fractional_factorial",
        "plackett_burman",
        "latin_hypercube",
        "central_composite",
        "box_behnken",
        "custom_optimal"
      ]
    },
    "factor_space": { "type": "object" },
    "target_runs": { "type": "integer", "minimum": 1 },
    "replicates": { "type": "integer", "default": 0 },
    "center_points": { "type": "integer", "default": 0 },
    "blocks": { "type": "integer", "default": 1 },
    "randomize": { "type": "boolean", "default": true },
    "seed": { "type": "integer" },
    "model_intent": {
      "enum": ["screening_main_effects", "two_factor_interactions", "quadratic_response_surface"]
    }
  }
}
```

**Output schema**

```json
{
  "type": "object",
  "required": ["study_id", "design_id", "design_matrix", "diagnostics"],
  "properties": {
    "study_id": { "type": "string" },
    "design_id": { "type": "string" },
    "design_matrix": {
      "type": "array",
      "items": { "type": "object" }
    },
    "diagnostics": {
      "type": "object",
      "properties": {
        "n_runs": { "type": "integer" },
        "estimable_terms": { "type": "array", "items": { "type": "string" } },
        "alias_warnings": { "type": "array", "items": { "type": "string" } },
        "power_notes": { "type": "array", "items": { "type": "string" } }
      }
    },
    "artifact_paths": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Side effects**
Writes `design_matrix.csv`, `design_metadata.json`, and audit log.

**Codex usage**
Use after factor validation. Codex should explain tradeoffs: run count, aliasing, randomization, center points, and what model can be supported.

---

### Tool: `fit_response_surface`

**Purpose**
Fit response models to observed experimental data.

**Input schema**

```json
{
  "type": "object",
  "required": ["study_id", "data"],
  "properties": {
    "study_id": { "type": "string" },
    "data": {
      "oneOf": [
        { "type": "string", "description": "Path to CSV/Parquet data file." },
        { "type": "array", "items": { "type": "object" } }
      ]
    },
    "responses": { "type": "array", "items": { "$ref": "#/ResponseSpec" } },
    "model_terms": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Example: A, B, A:B, I(A^2)"
    },
    "include_blocks": { "type": "boolean", "default": true },
    "robust_errors": { "type": "boolean", "default": true },
    "validation": {
      "enum": ["none", "loo", "kfold", "holdout"],
      "default": "loo"
    }
  }
}
```

**Output schema**

```json
{
  "type": "object",
  "required": ["study_id", "fit_id", "models", "diagnostics"],
  "properties": {
    "study_id": { "type": "string" },
    "fit_id": { "type": "string" },
    "models": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["response", "formula", "coefficients"],
        "properties": {
          "response": { "type": "string" },
          "formula": { "type": "string" },
          "coefficients": { "type": "array", "items": { "type": "object" } },
          "metrics": { "type": "object" },
          "warnings": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "diagnostics": { "type": "object" },
    "artifact_paths": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Side effects**
Writes `model_fit.json`, residual diagnostics, and audit log.

**Codex usage**
Use when observed data is provided. Codex should not overstate causal interpretation and should report model limitations.

---

### Tool: `analyze_effects`

**Purpose**
Calculate main effects, interactions, standardized effects, Pareto data, and factor-response curves.

**Input schema**

```json
{
  "type": "object",
  "required": ["study_id", "fit_id"],
  "properties": {
    "study_id": { "type": "string" },
    "fit_id": { "type": "string" },
    "effect_type": {
      "enum": ["main_effects", "interactions", "standardized", "all"],
      "default": "all"
    },
    "confidence_level": { "type": "number", "default": 0.95 },
    "prediction_grid": {
      "type": "object",
      "properties": {
        "points_per_factor": { "type": "integer", "default": 50 },
        "hold_strategy": { "enum": ["center", "best_observed", "user_specified"] },
        "hold_values": { "type": "object" }
      }
    }
  }
}
```

**Output schema**

```json
{
  "type": "object",
  "required": ["study_id", "effects", "plot_payloads"],
  "properties": {
    "study_id": { "type": "string" },
    "effects": { "type": "array", "items": { "type": "object" } },
    "plot_payloads": {
      "type": "object",
      "properties": {
        "pareto": { "type": "array", "items": { "type": "object" } },
        "factor_response": { "type": "array", "items": { "type": "object" } },
        "interaction_slices": { "type": "array", "items": { "type": "object" } }
      }
    },
    "warnings": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Side effects**
Writes `effects.json` and plot-ready payloads.

**Codex usage**
Use after model fit. Codex should use this for explanations and dashboard charts.

---

### Tool: `suggest_next_experiment`

**Purpose**
Recommend next experiments balancing predicted performance, uncertainty, feasibility, and COGS.

**Input schema**

```json
{
  "type": "object",
  "required": ["study_id", "fit_id", "objectives"],
  "properties": {
    "study_id": { "type": "string" },
    "fit_id": { "type": "string" },
    "objectives": { "type": "array", "items": { "$ref": "#/ResponseSpec" } },
    "constraints": { "type": "array", "items": { "type": "object" } },
    "n_recommendations": { "type": "integer", "default": 5 },
    "strategy": {
      "enum": ["desirability", "d_optimal_augment", "expected_improvement", "hybrid"],
      "default": "hybrid"
    },
    "exploration_weight": { "type": "number", "default": 0.2 },
    "avoid_duplicates": { "type": "boolean", "default": true },
    "seed": { "type": "integer" }
  }
}
```

**Output schema**

```json
{
  "type": "object",
  "required": ["study_id", "recommendations"],
  "properties": {
    "study_id": { "type": "string" },
    "recommendations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "run_id": { "type": "string" },
          "factor_settings": { "type": "object" },
          "predicted_responses": { "type": "object" },
          "desirability": { "type": "number" },
          "uncertainty_score": { "type": "number" },
          "feasibility_notes": { "type": "array", "items": { "type": "string" } },
          "rationale": { "type": "string" }
        }
      }
    },
    "warnings": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Side effects**
Writes `next_experiments.json`.

**Codex usage**
Use for “what should I run next?” prompts. Codex should explain why each run is exploitation, exploration, or constraint-probing.

---

### Tool: `calculate_cogs_impact`

**Purpose**
Estimate process economics and COGS impacts across factor settings or scenarios.

**Input schema**

```json
{
  "type": "object",
  "required": ["study_id"],
  "properties": {
    "study_id": { "type": "string" },
    "component_costs": {
      "type": "array",
      "description": "Direct user-provided prices. If omitted, economics is skipped.",
      "items": {
        "type": "object",
        "required": ["component_name", "unit_cost", "currency", "cost_basis_unit"],
        "properties": {
          "component_name": { "type": "string" },
          "unit_cost": { "type": "number" },
          "currency": { "type": "string" },
          "cost_basis_unit": { "type": "string", "description": "Example: EUR/mg, USD/U, USD/mL." },
          "factor_mapping": { "type": "string", "description": "Optional factor this component maps to, such as T7 RNAP or DNA template." },
          "fixed_amount_per_batch": { "type": "number" },
          "amount_unit": { "type": "string" },
          "price_low": { "type": "number" },
          "price_high": { "type": "number" }
        }
      }
    },
    "economics_assumptions": {
      "type": "object",
      "properties": {
        "basis": { "enum": ["per_batch", "per_g_product", "per_kg_product", "per_dose", "per_liter"] },
        "cost_efficiency_metric": { "enum": ["mass_per_currency", "currency_per_mass"], "default": "mass_per_currency" },
        "include_components": { "type": "array", "items": { "type": "string" } },
        "labor_rate": { "type": "number" },
        "overhead_multiplier": { "type": "number" },
        "batch_volume_l": { "type": "number" },
        "cycle_time_hr": { "type": "number" },
        "yield_model_response": { "type": "string" },
        "titer_model_response": { "type": "string" }
      }
    },
    "scenarios": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "scenario_id": { "type": "string" },
          "factor_settings": { "type": "object" }
        }
      }
    },
    "sensitivity": {
      "type": "object",
      "properties": {
        "parameters": { "type": "array", "items": { "type": "string" } },
        "percent_delta": { "type": "number", "default": 0.2 }
      }
    }
  }
}
```

**Output schema**

```json
{
  "type": "object",
  "required": ["study_id", "economics_status", "cogs_results"],
  "properties": {
    "study_id": { "type": "string" },
    "economics_status": {
      "enum": ["calculated", "skipped_missing_component_costs", "failed_validation"]
    },
    "cogs_results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "scenario_id": { "type": "string" },
          "factor_settings": { "type": "object" },
          "predicted_process_outputs": { "type": "object" },
          "cogs": { "type": "number" },
          "cost_efficiency": { "type": "number" },
          "currency": { "type": "string" },
          "cost_breakdown": { "type": "object" },
          "dominant_cost_drivers": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "cost_inputs_hash": { "type": "string" },
    "sensitivity_results": { "type": "object" },
    "warnings": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Side effects**
Writes `cogs.json`.

**Codex usage**
Use when user asks for cost/yield/tradeoff views or provides component costs. Codex should not invent prices. If `component_costs` is absent, Codex should say economics is unavailable for that run and continue with DOE/modeling outputs. Codex should label assumptions and avoid presenting early-stage COGS as validated finance.

---

### Tool: `generate_dashboard_payload`

**Purpose**
Collect current study artifacts into one versioned payload for the React app.

**Input schema**

```json
{
  "type": "object",
  "required": ["study_id"],
  "properties": {
    "study_id": { "type": "string" },
    "include": {
      "type": "array",
      "items": {
        "enum": [
          "factor_space",
          "design_matrix",
          "model_fit",
          "effects",
          "contours",
          "cogs",
          "next_experiments",
          "diagnostics"
        ]
      },
      "default": [
        "factor_space",
        "design_matrix",
        "model_fit",
        "effects",
        "contours",
        "cogs",
        "next_experiments",
        "diagnostics"
      ]
    },
    "payload_version": { "type": "string", "default": "1.0.0" }
  }
}
```

**Output schema**

```json
{
  "type": "object",
  "required": ["study_id", "payload_path", "payload_hash", "summary"],
  "properties": {
    "study_id": { "type": "string" },
    "payload_path": { "type": "string" },
    "payload_hash": { "type": "string" },
    "summary": { "type": "string" },
    "warnings": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Side effects**
Writes `dashboard_payload.json`.

**Codex usage**
Call after every analytical update before previewing the dashboard.

---

### Tool: `launch_dashboard_preview`

**Purpose**
Start or locate the dashboard dev server and return the route for the in-app browser.

**Input schema**

```json
{
  "type": "object",
  "required": ["study_id"],
  "properties": {
    "study_id": { "type": "string" },
    "host": { "type": "string", "default": "127.0.0.1" },
    "port": { "type": "integer", "default": 5173 },
    "mode": {
      "enum": ["return_url_only", "start_dev_server", "static_file"],
      "default": "return_url_only"
    },
    "reuse_existing": { "type": "boolean", "default": true }
  }
}
```

**Output schema**

```json
{
  "type": "object",
  "required": ["study_id", "url", "server_status"],
  "properties": {
    "study_id": { "type": "string" },
    "url": { "type": "string" },
    "server_status": {
      "enum": ["already_running", "started", "not_started", "failed"]
    },
    "pid": { "type": "integer" },
    "instructions": { "type": "string" },
    "warnings": { "type": "array", "items": { "type": "string" } }
  }
}
```

**Side effects**
Depending on `mode`, may start a local dev server. For safer MVP behavior, default to `return_url_only` and let Codex run the dev-server command in the integrated terminal or local environment action.

**Codex usage**
Codex should present the returned URL. The documented in-app browser can open the URL by click/manual navigation; a direct plugin API to force-open the in-app browser is not documented. ([OpenAI Developers][3])

---

## 8. React visualization architecture

### Routing model

```text
/
  Redirect to latest known study or empty state

/studies/:studyId
  Main dashboard for one study

/studies/:studyId/matrix
  Experiment matrix focused view

/studies/:studyId/effects
  Pareto and main-effect views

/studies/:studyId/contours
  Contour maps and COGS overlays

/studies/:studyId/scenarios
  Scenario comparison

/studies/:studyId/diagnostics
  Model diagnostics, warnings, audit metadata
```

### Component tree

```text
<App>
  <PayloadProvider>
    <StudyDashboard>
      <StudyHeader />
      <WarningBanner />
      <DashboardTabs>
        <ExperimentMatrix />
        <FactorResponsePanel>
          <FactorSelector />
          <ResponseSelector />
          <MainEffectChart />
          <InteractionSliceChart />
        </FactorResponsePanel>
        <ParetoEffectsChart />
        <ContourExplorer>
          <FactorPairSelector />
          <ContourMap />
          <CogsOverlay />
        </ContourExplorer>
        <ScenarioComparison>
          <ScenarioTable />
          <TradeoffScatter />
          <CostBreakdown />
        </ScenarioComparison>
        <NextExperimentQueue />
        <DiagnosticsPanel />
      </DashboardTabs>
      <PayloadFooter />
    </StudyDashboard>
  </PayloadProvider>
</App>
```

### Chart types

| View                | Chart                                          | Data source                      |
| ------------------- | ---------------------------------------------- | -------------------------------- |
| Experiment matrix   | sortable table / heatmap cells                 | `design_matrix`                  |
| Factor-response     | line/scatter with confidence bands             | `plot_payloads.factor_response`  |
| Pareto              | horizontal bar chart of standardized effects   | `plot_payloads.pareto`           |
| Contour map         | 2D response surface grid                       | `contours[]`                     |
| COGS overlay        | contour overlay / isolines / threshold regions | `cogs_results` + prediction grid |
| Scenario comparison | scatter, table, cost breakdown bars            | `scenarios[]`, `cogs_results[]`  |
| Next experiments    | ranked table with rationale                    | `recommendations[]`              |
| Diagnostics         | residual plots, warning list, audit metadata   | `diagnostics`                    |

### State model

Keep the React app mostly stateless.

```ts
type DashboardClientState = {
  selectedResponse: string;
  selectedFactorX: string;
  selectedFactorY: string;
  selectedScenarioIds: string[];
  matrixFilters: Record<string, unknown>;
  showConfidenceBands: boolean;
  showCogsOverlay: boolean;
};
```

Persistent scientific state should live in `dashboard_payload.json`, not React component state.

### Data contract

```ts
type DashboardPayload = {
  version: "1.0.0";
  study: {
    studyId: string;
    title: string;
    createdAt: string;
    updatedAt: string;
    runId: string;
  };
  factorSpace: {
    factors: FactorSpec[];
    constraints: ConstraintSpec[];
  };
  responses: ResponseSpec[];
  designMatrix?: {
    columns: string[];
    rows: ExperimentRow[];
    diagnostics: DesignDiagnostics;
  };
  modelFit?: {
    models: ResponseModel[];
    diagnostics: ModelDiagnostics;
  };
  effects?: {
    pareto: ParetoEffect[];
    factorResponse: FactorResponseCurve[];
    interactions: InteractionSlice[];
  };
  contours?: ContourPayload[];
  economics?: {
    assumptions: EconomicsAssumptions;
    cogsResults: CogsScenario[];
    overlays: CogsOverlayPayload[];
  };
  nextExperiments?: NextExperimentRecommendation[];
  warnings: WarningItem[];
  audit: {
    artifactHashes: Record<string, string>;
    generatedBy: string;
    generatedAt: string;
  };
};
```

### Browser preview behavior

Use one of two MVP-friendly approaches:

1. **Local dev server**
   Vite serves the React app. The app fetches payloads from a local static route or lightweight endpoint.

2. **File-backed static preview**
   MCP generates `dashboard.html` or a built static app that reads embedded JSON. This is simpler for locked-down environments but less interactive for iteration.

The in-app browser is documented for both local development servers and file-backed previews. ([OpenAI Developers][3])

### How Codex can safely regenerate/update the app

Use these guardrails:

```text
1. Shared JSON Schema is source of truth.
2. MCP validates payload before writing it.
3. React app validates payload at runtime.
4. Codex can update chart components only behind existing interfaces.
5. Codex must run:
   - Python tests for payload generation
   - TypeScript typecheck
   - dashboard build
6. Keep generated data separate from handwritten React code.
```

Recommended rules for `AGENTS.md` or the skill:

```text
- Never edit dashboard payloads by hand if an MCP tool can generate them.
- Never remove schema validation.
- When adding a chart, update:
  1. shared schema
  2. MCP payload generator
  3. React schema/type
  4. fixture payload
  5. component test
```

---

## 9. Codex interaction workflows

### Flow 1: “Design a screening DOE for 6 factors”

**User prompt**

```text
Use Scientific Toolchain to design a screening DOE for these 6 factors:
temperature 25-40 C, pH 6.5-7.5, feed rate 0.5-2.0 mL/min,
inducer 0-1 mM, media A/B/C, and agitation 200-800 rpm.
Responses are titer, impurity %, and viable cell density.
Open a dashboard I can review.
```

**High-level Codex/tool sequence**

```text
1. Codex invokes scientific-study-designer skill.
2. Codex normalizes factor specs and response goals.
3. MCP: validate_factor_space.
4. MCP: design_doe with screening_main_effects intent.
5. MCP: generate_dashboard_payload.
6. Codex starts or checks dashboard dev server.
7. MCP: launch_dashboard_preview.
8. Codex presents localhost URL for the in-app browser.
```

**React update behavior**

* Renders experiment matrix.
* Shows design diagnostics and alias warnings.
* Effects/model tabs show “waiting for observed data.”

**Browser behavior**

* User opens the returned local route in the Codex in-app browser.
* User comments on matrix columns, filters, or layout.
* Codex edits React components or regenerates payload.

---

### Flow 2: “Fit the uploaded data and explain main effects”

**User prompt**

```text
I uploaded observed_data.csv for the last DOE. Fit titer and impurity,
explain the main effects, and refresh the dashboard.
```

**High-level Codex/tool sequence**

```text
1. Codex reads/mentions uploaded CSV path.
2. MCP: validate_factor_space, using existing study artifacts.
3. MCP: fit_response_surface with responses titer and impurity.
4. MCP: analyze_effects.
5. MCP: generate_dashboard_payload.
6. MCP: launch_dashboard_preview.
7. Codex summarizes:
   - model terms
   - important effects
   - diagnostics
   - caveats
```

**React update behavior**

* Pareto chart populated.
* Factor-response plots populated.
* Diagnostics tab shows residual metrics and warnings.

**Browser behavior**

* User reviews the effects.
* User can comment “make impurity the default response” or “show only statistically strong effects.”
* Codex updates UI defaults or payload settings.

---

### Flow 3: “Show a contour map and COGS tradeoff”

**User prompt**

```text
Show a contour map for temperature vs pH on predicted titer,
overlay COGS assuming batch volume 50 L, resin cost 1200/kg,
media cost 80/L, labor 150/hr, and target minimum titer 2.5 g/L.
```

**High-level Codex/tool sequence**

```text
1. Codex checks that a fitted model exists.
2. MCP: calculate_cogs_impact with direct component costs and economics assumptions.
3. MCP: analyze_effects or contour-grid generation, if not already generated.
4. MCP: generate_dashboard_payload including contours and economics.
5. MCP: launch_dashboard_preview.
6. Codex explains assumptions and where COGS is model-based vs user-provided.
```

**React update behavior**

* Contour explorer opens to temperature vs pH.
* Titer response surface is shown.
* COGS threshold overlay appears.
* Scenario comparison tab lists best technical and best economic conditions.

**Browser behavior**

* User can visually inspect tradeoff regions.
* Browser comments can drive UI changes, such as “label the feasible low-COGS region.”

---

### Flow 4: “Propose the next 5 experiments and refresh the dashboard”

**User prompt**

```text
Propose the next 5 experiments. Balance improving titer,
reducing impurity, and lowering COGS. Refresh the dashboard.
```

**High-level Codex/tool sequence**

```text
1. Codex confirms current model and economics artifacts exist.
2. MCP: suggest_next_experiment with hybrid strategy.
3. MCP: generate_dashboard_payload.
4. MCP: launch_dashboard_preview.
5. Codex summarizes each recommended run:
   - factor settings
   - predicted response
   - uncertainty
   - COGS impact
   - rationale
```

**React update behavior**

* Next Experiment Queue tab shows ranked experiments.
* Scenario comparison adds current best, predicted best, and next-run candidates.

**Browser behavior**

* User reviews and asks for constraints, such as “avoid pH below 6.8.”
* Codex reruns `suggest_next_experiment` with updated constraints.

---

### Reference workflow target: IVT mRNA QbD DOE study

The product should be able to support, as a reference workflow, the IVT mRNA quality-by-design study described by Boman et al., "Quality by design approach to improve quality and decrease cost of in vitro transcription of mRNA using design of experiments."

**What that workflow requires**

```text
- Iterative D-optimal DOE, not only fixed full/fractional factorial designs.
- Candidate model terms covering main effects, interactions, and selected square terms.
- Factor transforms before later DOE iterations, such as log transforms for DNA and T7 RNAP.
- Time-resolved assay data, not only endpoint response rows.
- Endpoint quality responses, including semi-quantitative dsRNA scores and quality thresholds.
- Theoretical-yield calculation from mRNA sequence composition and limiting NTP.
- Relative yield as actual yield divided by theoretical maximum.
- Optional cost-efficiency response calculated only from user-supplied component prices.
- MLR response-surface fitting with heredity, parsimony, lack-of-fit, R2, Q2/predictive ability, and prediction intervals.
- Design-space estimation by probability of failure, such as Monte Carlo perturbation of factors against a dsRNA threshold.
- Desirability optimization constrained by the quality design space.
- Verification-run planning near design-space corners plus the predicted optimum.
- Construct-transfer analysis using sequence length, molarity, and time-scaling assumptions.
- Separate DOE templates for categorical/continuous follow-up studies, such as magnesium counterion by Mg:NTP ratio.
```

**Current architecture fit**

```text
Covered or mostly covered:
- factor validation
- DOE matrix generation
- response-surface fitting at a basic OLS level
- effect analysis and plots
- optional direct-input cost calculation
- desirability-style next-experiment suggestions
- React dashboard payload/rendering pattern

Not covered well enough yet:
- D-optimal design and full D-optimal augmentation
- iterative DOE campaigns with model updates between rounds
- time-resolved kinetic-response modeling
- IVT-specific theoretical yield and relative-yield calculations
- sequence-aware construct metadata
- Q2 / cross-validated predictive metrics as first-class outputs
- Monte Carlo design-space probability maps
- verification plan generation and prediction-interval checks
- construct-transfer modeling across mRNA lengths
- categorical counterion DOE templates
```

**Product changes needed to handle this paper-class workflow**

```text
1. Add an IVT/QbD study template in the skill references.
2. Add `design_optimal_doe` for launch D-optimal design and later full D-optimal augmentation from a candidate set.
3. Add `calculate_theoretical_yield` for sequence composition, limiting NTP, molecular weight, and relative yield.
4. Add `fit_time_resolved_response_model` for kinetic assay data and endpoint-derived responses.
5. Add `estimate_design_space_probability` for Monte Carlo probability-of-failure maps against quality limits.
6. Add `plan_verification_runs` for corner, edge, center, and predicted-optimum confirmation experiments.
7. Add `transfer_construct_model` for sequence-length and molarity adjusted prediction against a new construct.
8. Add `analyze_counterion_doe` or allow categorical factors cleanly in `design_optimal_doe`.
9. Extend dashboard views for time courses, design-space probability maps, relative-yield contours, cost-efficiency contours, and verification residuals.
```

**Launch bar**

At launch, the plugin should be able to execute the first practical slice of this workflow:

```text
- define the four-factor IVT knowledge space
- generate an initial D-optimal or fallback optimal-screening design
- accept time-resolved and endpoint assay data
- calculate theoretical and relative yield when sequence composition is supplied
- calculate cost efficiency when component costs are supplied
- fit and visualize yield, dsRNA, relative-yield, and cost-efficiency models
- state when any paper-level analysis is unavailable because inputs or validation data are missing
```

The launch product does not need to reproduce the paper's proprietary MODDE project or supporting-data tables exactly. It does need to reproduce the workflow class: iterative DOE, MLR response surfaces, quality-constrained design space, optional user-priced cost efficiency, and experimental verification planning.

---

## 10. Recommended MVP implementation plan

### Phase 0: proof of concept

**Scope**

* One repo.
* One plugin with one skill.
* Python MCP server with three tools:

  * `validate_factor_space`
  * `design_doe`
  * `generate_dashboard_payload`
* Shared schema scaffolding for optional component-cost inputs and cost-efficiency outputs.
* Minimal React dashboard:

  * experiment matrix
  * warnings panel
  * economics unavailable / available state
  * payload footer

**Build order**

```text
1. Define shared schemas.
2. Implement Python MCP server with FastMCP.
3. Configure MCP through `.codex/config.toml`.
4. Build dashboard shell.
5. Write skill instructions.
6. Install plugin through repo-local marketplace.
7. Test one prompt end to end.
```

**Tradeoffs**

* No model fitting yet.
* No full COGS optimization yet, but launch schemas and dashboard placeholders are present.
* Dashboard may be simple but proves the Codex loop.

**Risks**

* Plugin `.mcp.json` schema uncertainty.
* Local path resolution.
* Browser preview manual click/open step.

---

### Phase 1: working plugin + MCP + dashboard

**Scope**

* Plugin manifest, skill, MCP config.
* DOE generation for screening and simple response-surface designs.
* Model fit and effects tools.
* Optional component-cost calculation when user-provided prices are supplied.
* Dashboard tabs:

  * matrix
  * factor-response
  * Pareto
  * cost efficiency, when cost inputs exist
  * diagnostics

**Build order**

```text
1. Add D-optimal or candidate-set optimal DOE support.
2. Add model fitting.
3. Add effects analysis.
4. Add theoretical/relative-yield support for sequence-aware workflows.
5. Add optional component-cost calculation.
6. Expand dashboard schema.
7. Add chart components.
8. Add test fixtures.
9. Add local environment action for dashboard dev server.
10. Make `launch_dashboard_preview` return stable URL.
```

**Tradeoffs**

* Keep economics direct-input only; do not fetch, infer, or default reagent prices.
* Keep optimization heuristic-based.
* Avoid app/connector integrations.

**Risks**

* Statistical edge cases.
* Payload compatibility.
* Chart correctness.

---

### Phase 2: richer scientific workflows

**Scope**

* Richer COGS / process economics engine.
* Contour grids.
* Scenario comparison.
* Next-experiment optimization.
* Time-resolved kinetic modeling.
* Monte Carlo design-space probability maps.
* Verification-run planning.
* Construct-transfer analysis.
* Better diagnostics:

  * residual checks
  * leverage/outlier flags
  * alias/confounding notes
* Optional static HTML export.

**Build order**

```text
1. Expand launch cost-efficiency tool into scenario-level COGS.
2. Add time-resolved response modeling.
3. Add design-space probability estimation.
4. Add contour generator.
5. Add next-experiment tool.
6. Add verification-plan generation.
7. Add construct-transfer support.
8. Extend React scenario, contour, time-course, and verification views.
9. Add golden prompt tests.
```

**Tradeoffs**

* More science = more validation burden.
* Must avoid false precision.

**Risks**

* Economics assumptions misunderstood.
* Optimizer recommends infeasible or unsafe experiments.
* Codex over-interprets weak models.

---

### Phase 3: production hardening

**Scope**

* Internal package distribution.
* Hosted or internal HTTP MCP server.
* Access controls.
* Audit log and reproducibility reports.
* Validation against known DOE/modeling benchmarks.
* Optional automations for long-running studies.

**Build order**

```text
1. Add artifact hashing and provenance.
2. Add schema migrations.
3. Add permissions and secrets policy.
4. Add benchmark suite.
5. Add hosted dashboard mode.
6. Add team marketplace / distribution path.
```

**Tradeoffs**

* More operational overhead.
* Less solo-builder simplicity.

**Risks**

* Sensitive scientific data exposure.
* Permission drift.
* MCP server becomes too broad.
* Validation becomes a compliance concern.

---

## 11. Risk analysis

### Unsupported Codex UI assumptions

**Risk**
Trying to build a native embedded Codex plugin dashboard could waste time because Codex plugin docs do not document arbitrary embedded React UI surfaces.

**Mitigation**
Use the in-app browser. Treat “live visualization” as a local or hosted web preview, not a plugin-native panel.

---

### Local server / browser preview issues

**Risk**
The in-app browser does not support auth flows, signed-in pages, normal cookies, browser extensions, or existing tabs. ([OpenAI Developers][3])

**Mitigation**

```text
- Keep local dashboard unauthenticated.
- Bind to 127.0.0.1.
- Avoid secrets in query params.
- Use static payload files or local endpoints.
- Provide a clickable localhost URL.
```

---

### MCP tool complexity

**Risk**
One giant “analyze everything” tool becomes opaque, slow, and hard to debug.

**Mitigation**

```text
- Small tools with single responsibility.
- Typed input/output schemas.
- Per-tool audit logs.
- Deterministic seeds.
- Explicit warnings in every output.
```

---

### Scientific validation

**Risk**
The toolchain may generate statistically weak or inappropriate designs/models.

**Mitigation**

```text
- Encode design diagnostics.
- Return aliasing/power warnings.
- Block unsupported factor/model combinations.
- Add benchmark test fixtures.
- Require human review for final study plans.
```

---

### Reproducibility

**Risk**
Codex can edit files and rerun tools, but scientific outputs must be reproducible.

**Mitigation**

```text
- Store input hashes.
- Store package versions.
- Store random seeds.
- Store design/model/economics parameters.
- Use immutable run IDs.
- Write append-only audit logs.
```

---

### Model hallucination in scientific interpretation

**Risk**
Codex may explain results that were not computed or overstate inference.

**Mitigation**

```text
- Skill rule: no invented DOE matrices, coefficients, p-values, COGS, or recommendations.
- All numerical claims should trace to MCP artifacts.
- Dashboard and explanation should surface warnings.
- Include “what this does not prove” in summaries.
```

---

### Security of sensitive biotech data

**Risk**
Biotech/process datasets can be sensitive, and MCP tools may read/write local files or expose local dashboards.

**Mitigation**

```text
- Default to local-only stdio MCP.
- Bind dashboard to localhost.
- Avoid uploading data to hosted services unless explicitly approved.
- Redact secrets in logs.
- Do not paste secrets into browser flows.
- Use workspace-write sandbox and narrow approvals.
```

Codex docs emphasize that approvals and sandbox settings constrain actions, and that the sandbox controls directories and network access. ([OpenAI Developers][6])

---

## 12. Product boundaries

### Belongs in the plugin package

```text
- plugin manifest
- skill instructions
- skill metadata
- references and workflow checklists
- optional `.mcp.json` once verified
- install-surface assets
- local marketplace metadata for MVP
```

The plugin should **not** contain the heavy scientific engine unless packaging simplicity outweighs versioning clarity.

### Belongs in the MCP server

```text
- deterministic DOE generation
- factor validation
- model fitting
- effect analysis
- next-experiment optimization
- process economics
- artifact persistence
- schema validation
- audit logging
- dashboard payload generation
```

The MCP server is the scientific source of truth.

### Belongs in the React app

```text
- rendering
- filtering
- chart interaction
- client-side schema validation
- visual diagnostics
- local polling / refresh
- no scientific recomputation beyond display transforms
```

The React app should not compute final model fits or economics.

### Belongs in the Codex workflow

```text
- interpreting user intent
- choosing which skill/tool sequence to run
- editing app code
- running local commands/tests
- explaining outputs and limitations
- coordinating dashboard preview
```

Codex should orchestrate and explain, not silently invent computed results.

### Optional future extensions

```text
- hosted HTTP MCP server
- hosted dashboard
- authentication and RBAC
- electronic lab notebook integration
- LIMS integration
- batch record import
- automated nightly refits
- ChatGPT app iframe widget, if the product later targets ChatGPT rather than Codex
- subagents for separate statistics, economics, and UI passes
```

---

## 13. Opinionated recommendation

Build the **thin native Codex layer** first:

```text
1. One plugin.
2. One skill.
3. One local stdio Python MCP server.
4. One React dashboard route.
5. One dashboard payload schema.
6. One optional component-cost schema that never blocks DOE/modeling.
7. One local preview URL opened in the Codex in-app browser.
```

Do **not** overbuild a native Codex UI abstraction, app/connector integration, hosted MCP service, or multi-agent workflow at the start. The highest-leverage MVP is an end-to-end vertical slice:

```text
“Design a 6-factor screening DOE”
  → validate factor space
  → generate matrix
  → calculate cost efficiency only if direct component costs were supplied
  → write dashboard payload
  → render matrix in React
  → open localhost preview in Codex browser
```

Then add model fitting, Pareto charts, theoretical-yield calculations, and cost-efficiency views. After that, add contour maps, COGS overlays, time-resolved modeling, design-space probability, verification planning, and construct-transfer analysis. The architecture will feel native to Codex because Codex is doing what it is documented to do well: use skills, call MCP tools, edit code, run commands, and review a live web surface in the in-app browser.

[1]: https://developers.openai.com/codex/plugins "Plugins – Codex | OpenAI Developers"
[2]: https://developers.openai.com/codex/prompting "Prompting – Codex | OpenAI Developers"
[3]: https://developers.openai.com/codex/app/browser "In-app browser – Codex app | OpenAI Developers"
[4]: https://developers.openai.com/codex/plugins/build "Build plugins – Codex | OpenAI Developers"
[5]: https://developers.openai.com/codex/skills "Agent Skills – Codex | OpenAI Developers"
[6]: https://developers.openai.com/codex/app/features "Features – Codex app | OpenAI Developers"
[7]: https://modelcontextprotocol.io/specification/2025-06-18/server/tools "Tools - Model Context Protocol"
[8]: https://modelcontextprotocol.io/docs/develop/build-server "Build an MCP server - Model Context Protocol"
[9]: https://developers.openai.com/codex/app/automations "Automations – Codex app | OpenAI Developers"
[10]: https://developers.openai.com/codex/mcp "Model Context Protocol – Codex | OpenAI Developers"
