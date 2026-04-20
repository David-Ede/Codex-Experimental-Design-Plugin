# Security & Provenance Plan: Codex Scientific Toolchain

Date: 2026-04-20
Status: Draft for implementation planning
Related documents:

```text
- Technical Architecture Brief.md
- Product Requirements Document.md
- Data & Schema Contract.md
- MCP Tool API Spec.md
- Validation & Test Plan.md
- Implementation Roadmap.md
- Canonical Build Contract.md
```

## 1. Purpose

This document defines how the Codex Scientific Toolchain protects local scientific data, prevents unsafe file behavior, records provenance, preserves reproducibility, and makes generated analyses auditable.

The launch product is local-first. It does not require hosted storage, external price lookup, external sequence analysis, LIMS integration, ELN integration, or cloud execution. Security and provenance controls are therefore centered on:

```text
- safe local file handling
- deterministic artifact generation
- schema validation
- audit logging
- user-supplied cost provenance
- method and package version capture
- dashboard payload integrity
```

## 2. Security Goals

Security goals:

```text
1. Keep study data local by default.
2. Prevent tool calls from writing outside allowed project paths.
3. Prevent path traversal through user-supplied IDs, names, and file paths.
4. Prevent accidental or implied reagent price lookup.
5. Prevent construct sequences, observations, or cost tables from being transmitted externally by launch workflows.
6. Prevent dashboard rendering from executing user-provided content.
7. Preserve enough provenance to reproduce or audit every generated result.
8. Make missing or invalid provenance a release-blocking defect for derived scientific outputs.
```

## 3. Data Classification

| Data Type | Examples | Sensitivity | Launch Handling |
|---|---|---|---|
| Planning documents | product specs, method specs, setup guide | low to moderate | stored in repository |
| Study metadata | study title, description, owner label, domain | moderate | local artifact |
| Factor definitions | Mg:NTP range, NTP concentration range, enzyme range | moderate | local artifact |
| Response definitions | yield, dsRNA score, relative yield | moderate | local artifact |
| DOE matrices | planned experimental conditions | moderate to high | local artifact |
| Observations | endpoint and time-resolved assay data | high | local artifact |
| Construct sequences | mRNA/DNA sequence, poly(A) metadata | high | local artifact with redaction controls in logs |
| Component cost tables | reagent costs, enzyme costs, internal cost estimates | high | local artifact; never inferred |
| Model outputs | coefficients, diagnostics, predictions | high | local artifact |
| Dashboard payload | combined study state for UI | high | local artifact served locally |
| Audit logs | tool calls, hashes, artifact paths, warnings | high | local artifact |

## 4. Trust Boundaries

### 4.1 Trusted Components

Trusted local components:

```text
- Python MCP server code
- scientific engine modules
- schema validators
- artifact writer
- audit logger
- dashboard app code
- local validation scripts
```

### 4.2 Untrusted Inputs

The implementation must treat these as untrusted:

```text
- user-supplied study IDs
- user-supplied labels
- user-supplied factor names
- user-supplied response names
- imported CSV and JSON files
- construct sequences
- component cost tables
- dashboard route parameters
- local file paths passed through tool requests
```

### 4.3 Boundary Rules

Boundary rules:

```text
- Codex may orchestrate tools but must not be the source of numerical results.
- The dashboard may render payloads but must not compute scientific outputs.
- The backend may read user-specified input files only after path validation.
- The backend may write only to approved output directories.
- Launch workflows must not send study data to external services.
```

## 5. Local File Security

### 5.1 Allowed Write Roots

The backend may write generated files only under:

```text
outputs/studies/<study_id>/
validation-reports/
```

Development and test code may also write under:

```text
.pytest_cache/
apps/dashboard/test-results/
apps/dashboard/playwright-report/
```

The toolchain must never write generated scientific artifacts into:

```text
schemas/
fixtures/
planning documents
source code directories
parent directories outside the project
user home directories outside the project
system directories
```

### 5.2 Path Resolution

All file paths must be resolved through a single path utility with these rules:

```text
1. Resolve project root to an absolute canonical path.
2. Resolve requested path against the allowed root.
3. Normalize path separators.
4. Reject paths containing traversal segments after normalization.
5. Reject symlink escapes from allowed roots.
6. Reject absolute paths unless the specific tool explicitly accepts an import file.
7. For accepted import files, read-only access is allowed and writes remain restricted to outputs.
```

Study IDs must match:

```text
^[a-zA-Z0-9][a-zA-Z0-9_-]{1,80}$
```

Run IDs and artifact IDs must match:

```text
^[a-zA-Z0-9][a-zA-Z0-9_-]{1,120}$
```

### 5.3 Safe Write Policy

Safe write rules:

```text
- Write derived artifacts to a temporary file in the same directory.
- Flush and close the temporary file.
- Validate the artifact against schema where applicable.
- Compute output hash.
- Atomically rename the temporary file into place.
- Update latest pointers only after artifact write succeeds.
- Append audit log event after final status is known.
```

Overwrite behavior must follow the MCP `overwrite_policy`:

```text
write_new_run
replace_latest_pointer
fail_if_exists
```

No implementation path may silently replace historical run artifacts.

## 6. Input Sanitization

### 6.1 Labels and Display Text

User-provided labels may be stored and displayed, but must be escaped before rendering in HTML.

Examples:

```text
- study title
- factor display label
- response display label
- construct label
- component label
- imported column names
```

Dashboard rules:

```text
- render labels as text nodes, not HTML
- never use dangerouslySetInnerHTML for study content
- escape tooltip content
- keep raw labels out of CSS class names
- keep raw labels out of file paths
```

### 6.2 CSV and Spreadsheet Safety

CSV import rules:

```text
- Preserve raw values for provenance.
- Normalize scientific values into derived artifacts.
- Treat leading =, +, -, and @ in text fields as text, not formulas.
- When exporting CSV, prefix formula-like text fields with a single quote or use a safe CSV escaping policy.
- Do not evaluate formulas.
```

### 6.3 Sequence Handling

Sequence handling rules:

```text
- Validate sequence alphabet before downstream calculations.
- Store sequence length and composition in derived summaries.
- Avoid logging full raw sequences by default.
- Allow full sequence storage only in construct artifacts where required for reproducibility.
- Redact long sequences in error messages.
```

## 7. Network Policy

Launch network policy:

```text
- The MCP server does not require network access for launch workflows.
- The dashboard preview serves local assets and local payloads.
- Reagent prices are never fetched.
- Construct sequences are never sent to external services.
- Observation data is never uploaded.
- Cost tables are never uploaded.
```

Allowed network activity during development:

```text
- package installation from configured package registries
- developer-triggered documentation lookup
- developer-triggered deployment after explicit user request
```

Runtime tools must not perform network requests unless a later integration explicitly introduces a networked feature with its own security review.

## 8. Cost Data Controls

COGS behavior is a security and provenance concern because inferred or stale pricing can mislead scientific and economic decisions.

Rules:

```text
- Cost analysis is optional at runtime.
- Missing costs produce economics_status = unavailable.
- Missing costs do not block DOE generation, import, modeling, effects, recommendations, verification planning, or dashboard preview.
- Cost efficiency is calculated only from direct user-supplied component costs and usage formulas.
- The backend must never fetch reagent prices.
- The backend must never infer reagent prices from public sources.
- The backend must never use hidden default cost tables.
- Cost artifacts must record the source file or request that supplied each cost.
- Cost artifacts must record currency, quantity basis, component mapping, and timestamp.
```

Cost provenance fields:

```text
component_id
component_label
cost_value
cost_currency
cost_basis_quantity
cost_basis_unit
source_type
source_artifact
source_row
provided_at
provided_by_label
```

Invalid cost states:

```text
- negative cost
- missing currency
- missing basis quantity
- mixed currency without user-supplied conversion
- required component missing under complete-cost policy
- component usage missing under complete-usage policy
```

## 9. Provenance Model

### 9.1 Provenance Requirements

Every derived artifact must record:

```text
- schema_version
- method_version
- generated_at
- study_id
- run_id
- tool_name
- source_artifacts
- input_hash
- output_hash
- package_versions
- warnings
- unavailable_states
```

Every model artifact must also record:

```text
- model_formula
- encoded_terms
- factor_transforms
- response_id
- observation_artifact
- design_artifact
- fitting_method
- diagnostic_method
- confidence_level
```

Every stochastic artifact must also record:

```text
- seed
- random_generator
- sample_count
- selection_method
```

### 9.2 Source Artifact References

Source artifact references must include:

```text
- artifact_type
- artifact_path
- artifact_hash
- schema_version
- produced_by_tool
- produced_run_id
```

Derived artifacts must not reference only human-readable names. They must reference durable artifact paths and hashes.

### 9.3 Hashing Policy

Hashing rules:

```text
- Use SHA-256 for input_hash and output_hash.
- Canonicalize JSON before hashing.
- Normalize CSV line endings before hashing.
- Exclude generated_at from deterministic input hashes.
- Include method_version in input_hash for derived scientific outputs.
- Include source artifact hashes in input_hash.
- Store hash algorithm with the hash value.
```

Canonical JSON policy:

```text
- UTF-8 encoding
- sorted keys
- no insignificant whitespace
- explicit nulls only where schema allows null
- stable numeric formatting from the serialization library
```

### 9.4 Method Versioning

Method versions must change when:

```text
- DOE selection behavior changes
- factor encoding behavior changes
- theoretical-yield formula changes
- relative-yield formula changes
- regression fitting behavior changes
- diagnostic calculation changes
- cost calculation behavior changes
- recommendation scoring changes
- design-space classification changes
```

Method versions do not need to change for:

```text
- typo fixes in messages
- dashboard-only visual styling
- non-scientific refactors with identical golden outputs
```

## 10. Audit Log

### 10.1 Audit Event Schema

Each audit event must include:

```text
event_id
timestamp
study_id
run_id
tool_name
actor_type
request_hash
input_artifact_hashes
output_artifact_hashes
status
warnings
errors
artifact_paths
method_versions
package_versions
duration_ms
```

Allowed statuses:

```text
success
warning
skipped
failed
```

### 10.2 Audit Event Rules

Rules:

```text
- Each tool call writes exactly one final audit event.
- A dry run writes a dry-run audit event and no final scientific artifacts.
- A skipped optional analysis writes status = skipped.
- A failed validation writes status = failed.
- Audit logs are append-only under normal execution.
- Audit logs must never include full cost tables in error text.
- Audit logs must never include full long sequences in error text.
```

### 10.3 Audit Review

A user or reviewer must be able to answer:

```text
- Which source data produced this model?
- Which method version produced this result?
- Which package versions were installed?
- Which warnings were present?
- Was cost efficiency unavailable, skipped, or calculated?
- Which direct cost table produced economics outputs?
- Which dashboard payload is current?
```

## 11. Reproducibility Controls

Reproducibility controls:

```text
- lock Python dependencies
- lock dashboard dependencies
- record package versions in run metadata
- record method versions in derived artifacts
- require seeds for stochastic methods
- store source artifact hashes
- store generated outputs as durable artifacts
- test deterministic outputs under fixed seed
```

Reproducibility is considered broken when:

```text
- identical inputs and seeds produce materially different scientific outputs
- derived artifacts omit source hashes
- package versions are absent from model outputs
- method versions are absent from derived scientific artifacts
- dashboard displays a result without a source artifact reference
```

## 12. Dashboard Integrity

Dashboard integrity rules:

```text
- The dashboard consumes only dashboard_payload.json or equivalent generated payloads.
- The dashboard must not modify study artifacts.
- The dashboard must not calculate final scientific outputs.
- The dashboard may filter, sort, and format values.
- The dashboard must display payload generation time and source artifact summary.
- The dashboard must display stale or incompatible payload states.
- The dashboard must render warnings near the views where they affect interpretation.
```

Preview server rules:

```text
- bind to localhost by default
- serve only dashboard assets and selected payload
- avoid directory listing
- avoid serving arbitrary project files
- reject path traversal in payload route parameters
```

## 13. Secrets and Configuration

Launch workflows do not require secrets.

Configuration rules:

```text
- Do not require API keys for launch workflows.
- Do not store secrets in planning docs, fixtures, source code, or dashboard payloads.
- Use environment variables only for local development settings.
- Redact environment variables from logs unless explicitly allowlisted.
- Keep package registry credentials outside the repository.
```

If hosted integrations are added later, they require:

```text
- secret inventory
- access-control design
- network data-flow review
- audit update
- privacy review
- new validation tests
```

## 14. Data Retention and Deletion

Launch retention policy:

```text
- Study artifacts remain on the user's local filesystem until the user deletes them.
- The toolchain does not auto-delete historical run artifacts.
- Temporary files from failed writes are cleaned after failure is recorded.
- Validation reports remain under validation-reports/.
```

Deletion behavior:

```text
- Deleting a study directory removes local artifacts for that study.
- Deletion is a manual filesystem action at launch.
- A future delete-study tool must require explicit user confirmation and write a deletion audit record outside the deleted study directory.
```

## 15. Threat Scenarios and Controls

| Threat Scenario | Control |
|---|---|
| Malicious study ID attempts path traversal | ID regex, canonical path resolver, allowed roots |
| Imported CSV contains spreadsheet formula | safe CSV parsing and export escaping |
| Construct sequence leaks through logs | sequence redaction in logs and errors |
| User labels inject HTML into dashboard | escaped text rendering, no raw HTML |
| Missing costs are treated as zero | explicit economics unavailable state |
| External price lookup contaminates COGS | network-free runtime and no price-fetch code path |
| Dashboard shows stale payload | payload generated_at, source hashes, stale-state detection |
| Historical artifact overwritten | write_new_run default and overwrite policy tests |
| Model output loses source context | mandatory source_artifacts and input_hash |
| Symlink escapes output root | canonical path and symlink resolution |

## 16. Validation Requirements

Security and provenance tests are defined in Validation & Test Plan.md and must include:

```text
- path traversal rejection
- allowed root enforcement
- schema validation for provenance fields
- audit event creation for success, warning, skipped, and failed states
- hash stability tests
- no-cost workflow tests
- direct-cost provenance tests
- dashboard escaping tests
- local-only launch workflow tests
```

Release-blocking failures:

```text
- scientific artifact without source hashes
- scientific artifact without method version
- cost efficiency calculated without direct user costs
- unsafe write outside allowed roots
- dashboard rendering user content as HTML
- missing audit event for derived output
```

## 17. Future Hosted Mode Requirements

A hosted mode cannot reuse launch assumptions without additional controls. Before hosted operation, the project must add:

```text
- authentication
- authorization
- tenant isolation
- encrypted transport
- encrypted storage
- hosted audit storage
- retention policy
- deletion workflow
- secret management
- incident response process
- data-processing agreement review
- hosted dashboard access controls
```

Hosted mode must remain a separate release decision.

## 18. Final Security and Provenance Rule

The toolchain is acceptable only when a reviewer can trace every displayed scientific result back to source artifacts, method versions, package versions, warnings, and user-supplied assumptions. If provenance is incomplete, the result must be treated as unavailable or invalid, not merely undocumented.
