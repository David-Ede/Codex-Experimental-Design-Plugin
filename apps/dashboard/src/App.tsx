import { useMemo, useState } from "react";
import {
  type Availability,
  type DashboardPayload,
  type DesignRow,
  type FixtureName,
  defaultFixtureName,
  fixturePayloads,
  getFixtureNameFromLocation,
  validateDashboardPayload
} from "./payload";

type TabId =
  | "overview"
  | "matrix"
  | "time_courses"
  | "effects"
  | "relative_yield"
  | "economics"
  | "recommendations"
  | "verification"
  | "diagnostics";

const tabs: Array<{ id: TabId; label: string; section: string }> = [
  { id: "overview", label: "Overview", section: "diagnostics" },
  { id: "matrix", label: "Matrix", section: "experiment_matrix" },
  { id: "time_courses", label: "Time Courses", section: "time_courses" },
  { id: "effects", label: "Effects", section: "effects" },
  { id: "relative_yield", label: "Relative Yield", section: "relative_yield" },
  { id: "economics", label: "Economics", section: "economics" },
  { id: "recommendations", label: "Recommendations", section: "recommendations" },
  { id: "verification", label: "Verification", section: "verification" },
  { id: "diagnostics", label: "Diagnostics", section: "diagnostics" }
];

export default function App() {
  const fixtureName = useMemo(() => getFixtureNameFromLocation(window.location.search), []);
  const validation = useMemo(() => validateDashboardPayload(fixturePayloads[fixtureName]), [fixtureName]);
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  if (!validation.ok) {
    return <PayloadError fixtureName={fixtureName} errors={validation.errors} />;
  }

  if (!validation.data.study) {
    return <EmptyState payload={validation.data} fixtureName={fixtureName} />;
  }

  return (
    <div className="app-shell">
      <StudyHeader payload={validation.data} fixtureName={fixtureName} />
      <WarningStrip payload={validation.data} />
      <nav className="tabs" aria-label="Dashboard sections" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            aria-selected={activeTab === tab.id}
            className="tab"
            role="tab"
            type="button"
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.label}</span>
            <AvailabilityDot availability={validation.data.sections[tab.section]} />
          </button>
        ))}
      </nav>
      <main className="workspace">
        <DashboardContent payload={validation.data} activeTab={activeTab} />
      </main>
      <PayloadFooter payload={validation.data} />
    </div>
  );
}

function StudyHeader({ payload, fixtureName }: { payload: DashboardPayload; fixtureName: FixtureName }) {
  const study = payload.study;
  if (!study) {
    return null;
  }

  return (
    <header className="study-header">
      <div>
        <p className="eyebrow">DOE Scientific Toolchain</p>
        <h1>{study.title}</h1>
      </div>
      <dl className="header-facts" aria-label="Study facts">
        <Fact label="Study ID" value={study.study_id} />
        <Fact label="Domain" value={study.domain_template} />
        <Fact label="Design" value={study.active_design_id ?? "unavailable"} />
        <Fact label="Fit" value={study.active_fit_id ?? "unavailable"} />
        <Fact label="Payload" value={payload.payload_metadata.generated_at} />
        <Fact label="Fixture" value={fixtureName} />
      </dl>
    </header>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function WarningStrip({ payload }: { payload: DashboardPayload }) {
  const visibleWarnings = payload.warnings.filter((warning) => warning.severity !== "info");
  if (visibleWarnings.length === 0) {
    return (
      <section className="status-strip status-strip--clear" aria-label="Warnings">
        No blocking warnings in this fixture payload.
      </section>
    );
  }

  return (
    <section className="status-strip" aria-label="Warnings">
      {visibleWarnings.map((warning) => (
        <p key={`${warning.code}-${warning.field ?? "global"}`}>
          <strong>{warning.severity}</strong> {warning.code}: {warning.message}
        </p>
      ))}
    </section>
  );
}

function AvailabilityDot({ availability }: { availability?: Availability }) {
  const status = availability?.status ?? "unavailable_not_run";
  return <span className={`availability-dot availability-dot--${status}`} aria-label={status} />;
}

function DashboardContent({ payload, activeTab }: { payload: DashboardPayload; activeTab: TabId }) {
  if (activeTab === "overview") {
    return <Overview payload={payload} />;
  }
  if (activeTab === "matrix") {
    return <MatrixView payload={payload} />;
  }
  if (activeTab === "diagnostics") {
    return <Diagnostics payload={payload} />;
  }

  const section = tabs.find((tab) => tab.id === activeTab)?.section ?? activeTab;
  return (
    <AvailabilityPanel
      title={tabs.find((tab) => tab.id === activeTab)?.label ?? activeTab}
      availability={payload.sections[section]}
    />
  );
}

function Overview({ payload }: { payload: DashboardPayload }) {
  const factors = payload.factor_space?.factors ?? [];
  const firstDesign = payload.designs[0];
  const rows = firstDesign?.matrix ?? [];

  return (
    <section className="panel" aria-labelledby="overview-title">
      <div className="section-heading">
        <h2 id="overview-title">Study Status</h2>
        <p>Fixture-backed read model. Scientific sections remain unavailable until MCP tools produce artifacts.</p>
      </div>
      <div className="metric-grid">
        <Metric label="Factors" value={String(factors.length)} detail="validated fixture fields" />
        <Metric label="Responses" value={String(payload.responses.length)} detail="declared goals" />
        <Metric label="Rows" value={String(rows.length)} detail={firstDesign?.design_id ?? "no matrix"} />
        <Metric label="Warnings" value={String(payload.warnings.length)} detail="payload warnings" />
      </div>
      <div className="status-table-wrap">
        <table className="status-table">
          <thead>
            <tr>
              <th>Section</th>
              <th>Status</th>
              <th>Reason</th>
              <th>Required Inputs</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(payload.sections).map(([section, availability]) => (
              <tr key={section}>
                <td>{section}</td>
                <td>
                  <StatusBadge status={availability.status} />
                </td>
                <td>{availability.reason ?? "Available"}</td>
                <td>{availability.required_inputs.join(", ") || "none"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function MatrixView({ payload }: { payload: DashboardPayload }) {
  const factors = payload.factor_space?.factors ?? [];
  const design = payload.designs[0];
  const rows = design?.matrix ?? [];

  if (!design || rows.length === 0) {
    return <AvailabilityPanel title="Matrix" availability={payload.sections.experiment_matrix} />;
  }

  const columns = ["run_id", "run_type", "randomization_order", ...factors.map((factor) => factor.name)];

  return (
    <section className="panel" aria-labelledby="matrix-title">
      <div className="section-heading">
        <h2 id="matrix-title">Experiment Matrix</h2>
        <p>{design.design_id} renders fixture rows only. No DOE recomputation occurs in the dashboard.</p>
      </div>
      <div className="matrix-wrap">
        <table className="matrix-table">
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column}>{columnLabel(column, factors)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={String(row.run_id)}>
                {columns.map((column) => (
                  <td key={column}>{formatCell(row, column)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function columnLabel(column: string, factors: NonNullable<DashboardPayload["factor_space"]>["factors"]) {
  const factor = factors?.find((candidate) => candidate.name === column);
  return factor ? `${factor.display_name} (${factor.units})` : column;
}

function formatCell(row: DesignRow, column: string) {
  const value = row[column];
  if (value === null || value === undefined || value === "") {
    return "unavailable";
  }
  return String(value);
}

function AvailabilityPanel({ title, availability }: { title: string; availability?: Availability }) {
  const state = availability ?? {
    status: "unavailable_not_run" as const,
    reason: "This section has not been generated.",
    required_inputs: [],
    source_artifacts: []
  };

  return (
    <section className="panel panel--availability" aria-labelledby={`${title}-title`}>
      <div className="section-heading">
        <h2 id={`${title}-title`}>{title}</h2>
        <StatusBadge status={state.status} />
      </div>
      <p>{state.reason ?? "Available"}</p>
      <dl className="availability-details">
        <Fact label="Required inputs" value={state.required_inputs.join(", ") || "none"} />
        <Fact label="Source artifacts" value={state.source_artifacts.join(", ") || "none"} />
      </dl>
    </section>
  );
}

function Diagnostics({ payload }: { payload: DashboardPayload }) {
  return (
    <section className="panel" aria-labelledby="diagnostics-title">
      <div className="section-heading">
        <h2 id="diagnostics-title">Diagnostics</h2>
        <p>Payload validation, source artifacts, and audit metadata from the fixture payload.</p>
      </div>
      <div className="diagnostics-grid">
        <DiagnosticBlock title="Payload">
          <Fact label="Payload ID" value={payload.payload_metadata.payload_id} />
          <Fact label="Hash" value={payload.payload_metadata.payload_hash} />
          <Fact label="Schema" value={payload.payload_metadata.schema_version} />
        </DiagnosticBlock>
        <DiagnosticBlock title="Source Artifacts">
          {payload.payload_metadata.source_artifacts.length === 0 ? (
            <p>No source artifacts are listed.</p>
          ) : (
            <ul className="artifact-list">
              {payload.payload_metadata.source_artifacts.map((artifact) => (
                <li key={`${artifact.artifact_type}-${artifact.path}`}>
                  <strong>{artifact.artifact_type}</strong>
                  <span>{artifact.path}</span>
                </li>
              ))}
            </ul>
          )}
        </DiagnosticBlock>
      </div>
    </section>
  );
}

function DiagnosticBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="diagnostic-block">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

function StatusBadge({ status }: { status: Availability["status"] }) {
  return <span className={`status-badge status-badge--${status}`}>{status}</span>;
}

function PayloadFooter({ payload }: { payload: DashboardPayload }) {
  return (
    <footer className="payload-footer">
      <span>Payload {payload.payload_metadata.payload_id}</span>
      <span>{payload.payload_metadata.payload_hash}</span>
      <span>Generated by {String(payload.audit.generated_by ?? "unknown")}</span>
    </footer>
  );
}

function PayloadError({ fixtureName, errors }: { fixtureName: FixtureName; errors: string[] }) {
  return (
    <main className="app-shell app-shell--single">
      <section className="panel panel--error" aria-labelledby="payload-error-title">
        <p className="eyebrow">Payload validation error</p>
        <h1 id="payload-error-title">Fixture `{fixtureName}` cannot be rendered as a dashboard payload.</h1>
        <ul>
          {errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
        <p>Rendering is blocked so invalid scientific state is not displayed.</p>
      </section>
    </main>
  );
}

function EmptyState({ payload, fixtureName }: { payload: DashboardPayload; fixtureName: FixtureName }) {
  return (
    <main className="app-shell app-shell--single">
      <section className="panel panel--availability" aria-labelledby="empty-title">
        <p className="eyebrow">Fixture {fixtureName || defaultFixtureName}</p>
        <h1 id="empty-title">No study payload is available.</h1>
        <p>Run generate_dashboard_payload from Codex to create one.</p>
        <PayloadFooter payload={payload} />
      </section>
    </main>
  );
}
