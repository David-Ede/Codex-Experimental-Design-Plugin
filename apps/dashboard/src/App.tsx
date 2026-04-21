import { useEffect, useMemo, useState } from "react";
import {
  type Availability,
  type CandidateDesign,
  type CandidateStatus,
  type ContextualAIPanel,
  type DashboardPayload,
  type DesignRow,
  type RunPlanCommit,
  type StudySnapshot,
  type WorkbenchPayload,
  defaultFixtureName,
  fixturePayloads,
  getFixtureNameFromLocation,
  getPayloadUrlFromLocation,
  getStudyIdFromPathname,
  validateDashboardPayload
} from "./payload";

type TabId =
  | "workbench"
  | "overview"
  | "matrix"
  | "results"
  | "time_courses"
  | "effects"
  | "relative_yield"
  | "economics"
  | "recommendations"
  | "verification"
  | "diagnostics";

const tabs: Array<{ id: TabId; label: string; section: string }> = [
  { id: "workbench", label: "Workbench", section: "workbench" },
  { id: "overview", label: "Overview", section: "diagnostics" },
  { id: "matrix", label: "Matrix", section: "experiment_matrix" },
  { id: "results", label: "Results", section: "endpoint_results" },
  { id: "time_courses", label: "Time Courses", section: "time_courses" },
  { id: "effects", label: "Effects", section: "effects" },
  { id: "relative_yield", label: "Relative Yield", section: "relative_yield" },
  { id: "economics", label: "Economics", section: "economics" },
  { id: "recommendations", label: "Recommendations", section: "recommendations" },
  { id: "verification", label: "Verification", section: "verification" },
  { id: "diagnostics", label: "Diagnostics", section: "diagnostics" }
];

type DataRecord = Record<string, unknown>;

function isRecord(value: unknown): value is DataRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function getRecord(value: unknown): DataRecord | null {
  return isRecord(value) ? value : null;
}

function getRecordArray(value: unknown): DataRecord[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}

function getNestedRecord(source: DataRecord, key: string): DataRecord | null {
  return getRecord(source[key]);
}

function getNestedRecordArray(source: DataRecord, key: string): DataRecord[] {
  return getRecordArray(source[key]);
}

function getEndpointRows(payload: DashboardPayload): DataRecord[] {
  const endpoint = getRecord(payload.observations.endpoint);
  return endpoint ? getNestedRecordArray(endpoint, "rows") : [];
}

function getString(record: DataRecord, key: string, fallback = "unavailable"): string {
  const value = record[key];
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

function getNumber(record: DataRecord, key: string): number | null {
  const value = record[key];
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function getDisplayNumber(record: DataRecord, key: string, digits = 1): string {
  const value = getNumber(record, key);
  return value === null ? "unavailable" : value.toFixed(digits);
}

function formatValue(value: unknown, digits = 1): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return Number.isInteger(value) ? String(value) : value.toFixed(digits);
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  return "unavailable";
}

function formatSigned(value: number, digits = 1): string {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(digits)}`;
}

function clampPercent(value: number): number {
  return Math.min(100, Math.max(0, value));
}

function getSection(payload: DashboardPayload, section: string): Availability | undefined {
  return payload.sections[section];
}

function sectionIsAvailable(payload: DashboardPayload, section: string): boolean {
  return getSection(payload, section)?.status === "available";
}

type StatusKind = Availability["status"] | CandidateStatus | "current";

export default function App() {
  const fixtureName = useMemo(() => getFixtureNameFromLocation(window.location.search), []);
  const payloadUrl = useMemo(() => getPayloadUrlFromLocation(window.location.search), []);
  const routeStudyId = useMemo(() => getStudyIdFromPathname(window.location.pathname), []);
  const [rawPayload, setRawPayload] = useState<unknown | null>(
    payloadUrl ? null : fixturePayloads[fixtureName]
  );
  const [loadError, setLoadError] = useState<string | null>(null);
  const validation = useMemo(
    () => (rawPayload === null ? null : validateDashboardPayload(rawPayload)),
    [rawPayload]
  );
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const sourceLabel = payloadUrl ? `${routeStudyId ?? "payload"}:${payloadUrl}` : `fixture:${fixtureName}`;

  useEffect(() => {
    if (!payloadUrl) {
      setRawPayload(fixturePayloads[fixtureName]);
      setLoadError(null);
      return;
    }

    let cancelled = false;
    setRawPayload(null);
    setLoadError(null);
    fetch(payloadUrl)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`payload fetch failed with ${response.status}`);
        }
        return response.json();
      })
      .then((payload) => {
        if (!cancelled) {
          setRawPayload(payload);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setLoadError(error instanceof Error ? error.message : "payload fetch failed");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [fixtureName, payloadUrl]);

  useEffect(() => {
    if (validation?.ok && validation.data.workbench && activeTab === "overview") {
      setActiveTab("workbench");
    }
  }, [activeTab, validation]);

  if (loadError) {
    return <PayloadError sourceLabel={sourceLabel} errors={[loadError]} />;
  }

  if (validation === null) {
    return <PayloadLoading sourceLabel={sourceLabel} />;
  }

  if (!validation.ok) {
    return <PayloadError sourceLabel={sourceLabel} errors={validation.errors} />;
  }

  if (!validation.data.study) {
    return <EmptyState payload={validation.data} sourceLabel={sourceLabel} />;
  }

  return (
    <div className="app-shell">
      <Sidebar payload={validation.data} activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="dashboard-main">
        <TopBar payload={validation.data} sourceLabel={sourceLabel} />
        <StudyHeader payload={validation.data} sourceLabel={sourceLabel} />
        <WarningStrip payload={validation.data} />
        <main className={activeTab === "workbench" ? "workspace workspace--workbench" : "workspace"}>
          <DashboardContent payload={validation.data} activeTab={activeTab} />
        </main>
        <PayloadFooter payload={validation.data} />
      </div>
    </div>
  );
}

function Sidebar({
  payload,
  activeTab,
  setActiveTab
}: {
  payload: DashboardPayload;
  activeTab: TabId;
  setActiveTab: (tabId: TabId) => void;
}) {
  return (
    <aside className="sidebar" aria-label="Dashboard navigation">
      <div className="brand-lockup">
        <span className="brand-mark" aria-hidden="true">
          D
        </span>
        <strong>DOE Workbench</strong>
      </div>
      <div className="sidebar-search">Study object workspace</div>
      <nav className="sidebar-tabs" aria-label="Dashboard sections" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            aria-selected={activeTab === tab.id}
            className="sidebar-tab"
            role="tab"
            type="button"
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.label}</span>
            <AvailabilityDot availability={payload.sections[tab.section]} />
          </button>
        ))}
      </nav>
      <div className="sidebar-account">
        <span className="avatar" aria-hidden="true">
          DS
        </span>
        <div>
          <strong>{payload.study?.study_id ?? "No study"}</strong>
          <span>{payload.study?.status ?? "unavailable"}</span>
        </div>
      </div>
    </aside>
  );
}

function TopBar({ payload, sourceLabel }: { payload: DashboardPayload; sourceLabel: string }) {
  return (
    <div className="top-bar">
      <div className="breadcrumb">Workbench / Study</div>
      <div className="top-actions">
        <span className="top-pill">Source: {sourceLabel}</span>
        <span className="notification-dot" aria-label="Payload ready" />
        <span className="avatar avatar--small" aria-hidden="true">
          {payload.study?.study_id.slice(0, 2).toUpperCase() ?? "NA"}
        </span>
      </div>
    </div>
  );
}

function StudyHeader({ payload, sourceLabel }: { payload: DashboardPayload; sourceLabel: string }) {
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
        <Fact label="Source" value={sourceLabel} />
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
  if (activeTab === "workbench") {
    return payload.workbench ? (
      <WorkbenchView payload={payload} workbench={payload.workbench} />
    ) : (
      <AvailabilityPanel title="Workbench" availability={payload.sections.workbench} />
    );
  }
  if (activeTab === "overview") {
    return <Overview payload={payload} />;
  }
  if (activeTab === "matrix") {
    return <MatrixView payload={payload} />;
  }
  if (activeTab === "results") {
    return sectionIsAvailable(payload, "endpoint_results") ? (
      <ResultsView payload={payload} />
    ) : (
      <AvailabilityPanel title="Results" availability={payload.sections.endpoint_results} />
    );
  }
  if (activeTab === "effects") {
    return sectionIsAvailable(payload, "effects") ? (
      <EffectsView payload={payload} />
    ) : (
      <AvailabilityPanel title="Effects" availability={payload.sections.effects} />
    );
  }
  if (activeTab === "relative_yield") {
    return sectionIsAvailable(payload, "relative_yield") ? (
      <RelativeYieldView payload={payload} />
    ) : (
      <AvailabilityPanel title="Relative Yield" availability={payload.sections.relative_yield} />
    );
  }
  if (activeTab === "recommendations") {
    return sectionIsAvailable(payload, "recommendations") ? (
      <RecommendationsView payload={payload} />
    ) : (
      <AvailabilityPanel title="Recommendations" availability={payload.sections.recommendations} />
    );
  }
  if (activeTab === "verification") {
    return sectionIsAvailable(payload, "verification") ? (
      <VerificationView payload={payload} />
    ) : (
      <AvailabilityPanel title="Verification" availability={payload.sections.verification} />
    );
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

export function WorkbenchView({
  payload,
  workbench
}: {
  payload: DashboardPayload;
  workbench: WorkbenchPayload;
}) {
  const candidateSet = workbench.candidate_design_sets[0];
  const candidates = candidateSet?.candidates ?? [];
  const preferredId =
    workbench.active_comparison?.preferred_candidate_design_id ??
    candidateSet?.ranking_summary.preferred_candidate_design_id ??
    candidates[0]?.candidate_design_id;
  const selected = candidates.find((candidate) => candidate.candidate_design_id === preferredId) ?? candidates[0];
  const advisorPanel =
    workbench.contextual_ai_panels.find((panel) => panel.object_id === selected?.candidate_design_id) ??
    workbench.contextual_ai_panels[0];

  return (
    <div className="workbench-layout">
      <aside className="study-rail" aria-label="Study stages">
        <p className="eyebrow">Study Stage</p>
        <h2>{workbench.study_stage.replaceAll("_", " ")}</h2>
        <StageList workbench={workbench} />
        <div className="snapshot-box">
          <span>Snapshots</span>
          <strong>{workbench.snapshots.length}</strong>
          <SnapshotList snapshots={workbench.snapshots} />
        </div>
      </aside>

      <section className="workbench-center" aria-labelledby="workbench-title">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Candidate Design Comparison</p>
            <h2 id="workbench-title">{payload.study?.title ?? "Workbench"}</h2>
            <p>{candidateSet?.ranking_summary.ranking_basis ?? "Candidate comparison is unavailable."}</p>
          </div>
          <StatusBadge status={payload.sections.workbench?.status ?? "unavailable_not_run"} />
        </div>

        <div className="workbench-summary">
          <Metric label="Mode" value={workbench.recommendation_mode.replaceAll("_", " ")} detail="ranking objective" />
          <Metric label="Candidates" value={String(candidates.length)} detail={candidateSet?.candidate_set_id ?? "none"} />
          <Metric
            label="Preferred"
            value={selected?.design_family.replaceAll("_", " ") ?? "none"}
            detail={selected?.candidate_design_id ?? "not selected"}
          />
          <Metric
            label="Committed"
            value={workbench.committed_run_plan ? workbench.committed_run_plan.run_plan_id : "none"}
            detail={workbench.committed_run_plan ? `${workbench.committed_run_plan.run_count} planned runs` : "run plan not committed"}
          />
        </div>

        <CandidateDesignGrid candidates={candidates} preferredId={preferredId ?? null} />
        <DesignComparisonTable candidates={candidates} />
        {selected ? <LearnCannotLearnPanel candidate={selected} /> : null}
        {workbench.committed_run_plan ? <CommittedRunPlanPanel runPlan={workbench.committed_run_plan} /> : null}
      </section>

      <AIAdvisorRail panel={advisorPanel} selected={selected} />

      <section className="workbench-drawer" aria-label="Workbench diagnostics">
        <div>
          <strong>Stale state</strong>
          <span>{workbench.stale_state.is_stale ? workbench.stale_state.stale_due_to.join(", ") : "current"}</span>
          {workbench.stale_state.affected_objects.length > 0 ? (
            <span>
              {workbench.stale_state.affected_objects
                .map((object) => `${object.object_type}:${object.object_id}`)
                .join(", ")}
            </span>
          ) : null}
        </div>
        <div>
          <strong>Source artifacts</strong>
          <SourceArtifactSummary
            selected={selected}
            runPlan={workbench.committed_run_plan}
            candidateSetPath={payload.sections.workbench?.source_artifacts ?? []}
          />
        </div>
      </section>
    </div>
  );
}

function StageList({ workbench }: { workbench: WorkbenchPayload }) {
  const stages = [
    "validated_setup",
    "candidates_generated",
    "candidates_compared",
    "run_plan_committed"
  ];

  return (
    <ol className="stage-list">
      {stages.map((stage) => {
        const isActive = stage === workbench.study_stage;
        const activeIndex = Math.max(0, stages.indexOf(workbench.study_stage));
        const isComplete = stages.indexOf(stage) < activeIndex;
        return (
          <li className={isActive ? "stage-list__item stage-list__item--active" : "stage-list__item"} key={stage}>
            <span aria-hidden="true">{isComplete ? "done" : "-"}</span>
            {stage.replaceAll("_", " ")}
          </li>
        );
      })}
    </ol>
  );
}

function SnapshotList({ snapshots }: { snapshots: StudySnapshot[] }) {
  if (snapshots.length === 0) {
    return <span className="muted-line">No snapshots yet</span>;
  }

  return (
    <ul className="snapshot-list" aria-label="Study snapshots">
      {snapshots.slice(-3).map((snapshot) => (
        <li key={snapshot.snapshot_id}>
          <strong>{snapshot.label}</strong>
          <span>{snapshot.committed_run_plan_id ?? snapshot.active_comparison_id ?? snapshot.active_candidate_set_id ?? "setup only"}</span>
        </li>
      ))}
    </ul>
  );
}

function SourceArtifactSummary({
  selected,
  runPlan,
  candidateSetPath
}: {
  selected?: CandidateDesign;
  runPlan: RunPlanCommit | null;
  candidateSetPath: string[];
}) {
  const refs = [
    ...candidateSetPath,
    ...(selected?.source_artifacts.map((artifact) => artifact.path) ?? []),
    ...(runPlan?.source_artifacts ?? [])
  ];
  const uniqueRefs = Array.from(new Set(refs));

  if (uniqueRefs.length === 0) {
    return <span>none</span>;
  }

  return (
    <>
      {uniqueRefs.slice(0, 6).map((ref) => (
        <span key={ref}>{ref}</span>
      ))}
    </>
  );
}

function CandidateDesignGrid({
  candidates,
  preferredId
}: {
  candidates: CandidateDesign[];
  preferredId: string | null;
}) {
  return (
    <div className="candidate-grid" aria-label="Candidate designs">
      {candidates.map((candidate) => (
        <article
          className={
            candidate.candidate_design_id === preferredId
              ? "candidate-card candidate-card--preferred"
              : "candidate-card"
          }
          key={candidate.candidate_design_id}
        >
          <div className="candidate-card__header">
            <div>
              <span className="eyebrow">{candidate.design_family.replaceAll("_", " ")}</span>
              <h3>{candidate.recommendation_label}</h3>
            </div>
            <StatusBadge status={candidate.status} />
          </div>
          <div className="candidate-metrics">
            <span>
              <strong>{candidate.run_count ?? "n/a"}</strong>
              runs
            </span>
            <span>
              <strong>{candidate.ranking_score === null ? "n/a" : candidate.ranking_score.toFixed(2)}</strong>
              score
            </span>
            <span>
              <strong>
                {candidate.diagnostics.condition_number === null
                  ? "n/a"
                  : candidate.diagnostics.condition_number.toFixed(1)}
              </strong>
              condition
            </span>
          </div>
          <ul className="compact-list">
            {(candidate.best_for ?? []).slice(0, 3).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          {candidate.unavailable_reasons.length > 0 ? (
            <div className="candidate-reasons" aria-label="Unavailable reasons">
              {candidate.unavailable_reasons.map((reason) => (
                <span key={reason}>{reason.replaceAll("_", " ")}</span>
              ))}
            </div>
          ) : null}
          {candidate.warnings.length > 0 ? (
            <div className="candidate-warning-list" aria-label="Candidate warnings">
              {candidate.warnings.map((warning) => (
                <span key={`${candidate.candidate_design_id}-${warning.code}`}>{warning.message}</span>
              ))}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}

function DesignComparisonTable({ candidates }: { candidates: CandidateDesign[] }) {
  const rows = [
    ["Runs", (candidate: CandidateDesign) => formatValue(candidate.run_count, 0)],
    ["Main effects", (candidate: CandidateDesign) => candidate.capabilities.main_effects],
    ["Interactions", (candidate: CandidateDesign) => candidate.capabilities.two_factor_interactions],
    ["Curvature", (candidate: CandidateDesign) => candidate.capabilities.curvature_detection],
    ["Pure error", (candidate: CandidateDesign) => candidate.capabilities.pure_error_estimate],
    [
      "Estimable terms",
      (candidate: CandidateDesign) =>
        candidate.diagnostics.estimable_term_fraction === null
          ? "unknown"
          : `${Math.round(candidate.diagnostics.estimable_term_fraction * 100)}%`
    ]
  ] as const;

  return (
    <section className="comparison-panel" aria-labelledby="comparison-title">
      <div className="section-heading section-heading--compact">
        <h3 id="comparison-title">Side-by-side comparison</h3>
        <span className="top-pill">computed payload</span>
      </div>
      <div className="matrix-wrap">
        <table className="matrix-table">
          <thead>
            <tr>
              <th>Metric</th>
              {candidates.map((candidate) => (
                <th key={candidate.candidate_design_id}>{candidate.design_family.replaceAll("_", " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, getter]) => (
              <tr key={label}>
                <td>{label}</td>
                {candidates.map((candidate) => (
                  <td key={`${candidate.candidate_design_id}-${label}`}>
                    <CapabilityText value={getter(candidate)} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CapabilityText({ value }: { value: string }) {
  const normalized = value.replaceAll("_", " ");
  return <span className={`capability-text capability-text--${value}`}>{normalized}</span>;
}

function LearnCannotLearnPanel({ candidate }: { candidate: CandidateDesign }) {
  return (
    <section className="learn-panel" aria-label="What this design can and cannot learn">
      <div>
        <h3>Can Learn</h3>
        <ul className="compact-list">
          {candidate.learnability.learnable.map((item) => (
            <li key={item.claim}>
              {item.label}
              <small>{item.source_ref}</small>
            </li>
          ))}
        </ul>
      </div>
      <div>
        <h3>Cannot Learn</h3>
        <ul className="compact-list">
          {candidate.learnability.not_learnable.map((item) => (
            <li key={item.claim}>
              {item.label}
              <small>{item.source_ref}</small>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function CommittedRunPlanPanel({ runPlan }: { runPlan: RunPlanCommit }) {
  return (
    <section className="run-plan-panel" aria-labelledby="run-plan-title">
      <div className="section-heading section-heading--compact">
        <div>
          <h3 id="run-plan-title">Committed Run Plan</h3>
          <p>{runPlan.source_candidate_design_id} is locked as an executable plan.</p>
        </div>
        <StatusBadge status="current" />
      </div>
      <div className="run-plan-grid">
        <Fact label="Run plan" value={runPlan.run_plan_id} />
        <Fact label="Runs" value={String(runPlan.run_count)} />
        <Fact label="Comparison" value={runPlan.source_comparison_id} />
        <Fact label="Matrix" value={runPlan.run_matrix_path} />
        <Fact label="Protocol notes" value={runPlan.protocol_notes_path} />
      </div>
    </section>
  );
}

function AIAdvisorRail({
  panel,
  selected
}: {
  panel?: ContextualAIPanel;
  selected?: CandidateDesign;
}) {
  if (!panel || !selected) {
    return (
      <aside className="advisor-rail" aria-label="AI advisor">
        <p className="eyebrow">AI Advisor</p>
        <h2>No explanation panel</h2>
        <p>Generate a contextual AI panel with source refs to populate this rail.</p>
      </aside>
    );
  }

  return (
    <aside className="advisor-rail" aria-label="AI advisor">
      <p className="eyebrow">AI Advisor</p>
      <h2>{panel.title}</h2>
      <p>{panel.summary}</p>
      <AdvisorList title="Best for" items={panel.best_for} />
      <AdvisorList title="Tradeoffs" items={panel.tradeoffs} />
      <AdvisorList title="Watch out for" items={panel.watch_out_for} />
      <div className="source-ref-box">
        <strong>Source refs</strong>
        {panel.source_refs.map((ref) => (
          <span key={ref}>{ref}</span>
        ))}
      </div>
    </aside>
  );
}

function AdvisorList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="advisor-list">
      <strong>{title}</strong>
      <ul className="compact-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
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
      <OverviewVisuals payload={payload} />
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

function OverviewVisuals({ payload }: { payload: DashboardPayload }) {
  const sections = Object.values(payload.sections);
  const availableCount = sections.filter((section) => section.status === "available").length;
  const totalCount = sections.length || 1;
  const availablePercent = Math.round((availableCount / totalCount) * 100);

  return (
    <div className="visual-grid" aria-label="Dashboard visual summaries">
      <section className="visual-card" aria-label="Gate availability">
        <div className="section-heading section-heading--compact">
          <h3>Gate availability</h3>
          <span className="top-pill">{availablePercent}% available</span>
        </div>
        <div className="donut-wrap">
          <div className="donut" style={{ "--value": `${availablePercent}%` } as React.CSSProperties}>
            <strong>{availableCount}</strong>
            <span>of {totalCount}</span>
          </div>
          <div className="donut-legend">
            <span>Available sections</span>
            <span>Unavailable states remain explicit</span>
          </div>
        </div>
      </section>
      <section className="visual-card" aria-label="Artifact coverage">
        <div className="section-heading section-heading--compact">
          <h3>Artifact coverage</h3>
          <span className="top-pill">{payload.payload_metadata.source_artifacts.length} sources</span>
        </div>
        <div className="bar-stack" aria-hidden="true">
          {payload.payload_metadata.source_artifacts.map((artifact, index) => (
            <span
              key={`${artifact.artifact_type}-${artifact.path}`}
              style={{ width: `${46 + index * 16}%` }}
            />
          ))}
          {payload.payload_metadata.source_artifacts.length === 0 ? <span style={{ width: "18%" }} /> : null}
        </div>
      </section>
    </div>
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

function ResultsView({ payload }: { payload: DashboardPayload }) {
  const rows = getEndpointRows(payload);
  const scoredRows = rows
    .map((row) => ({ row, score: getNumber(row, "overall_sensory_score") }))
    .filter((item): item is { row: DataRecord; score: number } => item.score !== null);
  const best = scoredRows.reduce<{ row: DataRecord; score: number } | null>(
    (current, candidate) => (!current || candidate.score > current.score ? candidate : current),
    null
  );
  const average =
    scoredRows.length > 0
      ? scoredRows.reduce((total, item) => total + item.score, 0) / scoredRows.length
      : null;

  if (rows.length === 0) {
    return <AvailabilityPanel title="Results" availability={payload.sections.endpoint_results} />;
  }

  return (
    <section className="panel" aria-labelledby="results-title">
      <div className="section-heading">
        <div>
          <h2 id="results-title">Dummy Endpoint Results</h2>
          <p>Hand-authored latte outcomes used to exercise the analytics UI. No model fit was run.</p>
        </div>
        <StatusBadge status={payload.sections.endpoint_results.status} />
      </div>
      <div className="metric-grid">
        <Metric label="Best run" value={getString(best?.row ?? {}, "run_id")} detail="highest dummy score" />
        <Metric label="Best score" value={best ? best.score.toFixed(1) : "n/a"} detail="overall sensory" />
        <Metric label="Mean score" value={average === null ? "n/a" : average.toFixed(1)} detail="12 dummy runs" />
        <Metric label="Observed rows" value={String(rows.length)} detail="endpoint observations" />
      </div>
      <div className="analytics-grid analytics-grid--wide-first">
        <section className="analytics-block" aria-label="Overall score by run">
          <div className="section-heading section-heading--compact">
            <h3>Overall Score By Run</h3>
            <span className="top-pill">0-10 scale</span>
          </div>
          <RunScoreChart rows={rows} bestRunId={getString(best?.row ?? {}, "run_id", "")} />
        </section>
        <section className="analytics-block" aria-label="Response snapshot">
          <div className="section-heading section-heading--compact">
            <h3>Response Snapshot</h3>
            <span className="top-pill">selected run</span>
          </div>
          <ResponseSnapshot row={best?.row ?? rows[0]} />
        </section>
      </div>
      <EndpointTable rows={rows} />
    </section>
  );
}

function RunScoreChart({ rows, bestRunId }: { rows: DataRecord[]; bestRunId: string }) {
  return (
    <div className="score-chart" role="img" aria-label="Bar chart of overall sensory score by run">
      {rows.map((row) => {
        const runId = getString(row, "run_id");
        const score = getNumber(row, "overall_sensory_score") ?? 0;
        return (
          <div className="score-column" key={runId}>
            <div className="score-bar-shell">
              <span
                className={runId === bestRunId ? "score-bar score-bar--best" : "score-bar"}
                style={{ height: `${clampPercent(score * 10)}%` }}
              >
                <strong>{score.toFixed(1)}</strong>
              </span>
            </div>
            <small>{runId.replace("run_", "")}</small>
          </div>
        );
      })}
    </div>
  );
}

function ResponseSnapshot({ row }: { row: DataRecord }) {
  const responses = [
    ["Overall", "overall_sensory_score"],
    ["Espresso", "espresso_balance_score"],
    ["Milk", "milk_texture_score"],
    ["Pour", "latte_art_pourability_score"]
  ] as const;

  return (
    <div className="response-bars">
      <strong>{getString(row, "run_id")}</strong>
      {responses.map(([label, key]) => {
        const value = getNumber(row, key) ?? 0;
        return (
          <div className="response-bar-row" key={key}>
            <span>{label}</span>
            <div className="response-track">
              <span style={{ width: `${clampPercent(value * 10)}%` }} />
            </div>
            <b>{value.toFixed(1)}</b>
          </div>
        );
      })}
    </div>
  );
}

function EndpointTable({ rows }: { rows: DataRecord[] }) {
  const columns = [
    "run_id",
    "overall_sensory_score",
    "espresso_balance_score",
    "milk_texture_score",
    "latte_art_pourability_score",
    "shot_time_s",
    "extraction_yield_percent"
  ];

  return (
    <div className="matrix-wrap analytics-table-wrap">
      <table className="matrix-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={getString(row, "run_id")}>
              {columns.map((column) => (
                <td key={column}>{formatValue(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EffectsView({ payload }: { payload: DashboardPayload }) {
  const effects = getRecord(payload.derived.effects);
  if (!effects) {
    return <AvailabilityPanel title="Effects" availability={payload.sections.effects} />;
  }

  const mainEffects = getNestedRecordArray(effects, "main_effects");
  const interactions = getNestedRecordArray(effects, "interaction_pairs");
  const curves = getNestedRecordArray(effects, "response_curves");

  return (
    <section className="panel" aria-labelledby="effects-title">
      <div className="section-heading">
        <div>
          <h2 id="effects-title">Dummy Effect Analytics</h2>
          <p>{getString(effects, "note", "Illustrative effect summaries only.")}</p>
        </div>
        <StatusBadge status={payload.sections.effects.status} />
      </div>
      <div className="analytics-grid">
        <section className="analytics-block" aria-label="Main effect ranking">
          <div className="section-heading section-heading--compact">
            <h3>Main Effect Ranking</h3>
            <span className="top-pill">dummy effect size</span>
          </div>
          <EffectBars effects={mainEffects} />
        </section>
        <section className="analytics-block" aria-label="Interaction strength">
          <div className="section-heading section-heading--compact">
            <h3>Interaction Strength</h3>
            <span className="top-pill">relative</span>
          </div>
          <InteractionList interactions={interactions} />
        </section>
      </div>
      <div className="curve-grid">
        {curves.map((curve) => (
          <ResponseCurve key={getString(curve, "factor")} curve={curve} />
        ))}
      </div>
    </section>
  );
}

function EffectBars({ effects }: { effects: DataRecord[] }) {
  const maxAbs = Math.max(1, ...effects.map((effect) => Math.abs(getNumber(effect, "effect") ?? 0)));

  return (
    <div className="effect-list">
      {effects.map((effect) => {
        const value = getNumber(effect, "effect") ?? 0;
        const isNegative = value < 0;
        return (
          <div className="effect-row" key={`${getString(effect, "factor")}-${getString(effect, "response")}`}>
            <span>{getString(effect, "display_name")}</span>
            <div className={isNegative ? "effect-track effect-track--negative" : "effect-track"}>
              <i style={{ width: `${clampPercent((Math.abs(value) / maxAbs) * 100)}%` }} />
            </div>
            <strong>{formatSigned(value)}</strong>
          </div>
        );
      })}
    </div>
  );
}

function InteractionList({ interactions }: { interactions: DataRecord[] }) {
  return (
    <div className="interaction-list">
      {interactions.map((interaction) => {
        const strength = getNumber(interaction, "strength") ?? 0;
        return (
          <div className="interaction-row" key={getString(interaction, "label")}>
            <span>{getString(interaction, "label")}</span>
            <div className="interaction-meter">
              <span style={{ width: `${clampPercent(strength * 100)}%` }} />
            </div>
            <strong>{strength.toFixed(2)}</strong>
          </div>
        );
      })}
    </div>
  );
}

function ResponseCurve({ curve }: { curve: DataRecord }) {
  const points = getNestedRecordArray(curve, "points")
    .map((point) => ({
      x: getNumber(point, "x"),
      y: getNumber(point, "y")
    }))
    .filter((point): point is { x: number; y: number } => point.x !== null && point.y !== null);
  const xValues = points.map((point) => point.x);
  const yValues = points.map((point) => point.y);
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const width = 320;
  const height = 150;
  const pad = 18;
  const xSpan = Math.max(1, xMax - xMin);
  const ySpan = Math.max(1, yMax - yMin);
  const polyline = points
    .map((point) => {
      const x = pad + ((point.x - xMin) / xSpan) * (width - pad * 2);
      const y = height - pad - ((point.y - yMin) / ySpan) * (height - pad * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <section className="analytics-block curve-block" aria-label={`${getString(curve, "display_name")} curve`}>
      <div className="section-heading section-heading--compact">
        <h3>{getString(curve, "display_name")}</h3>
        <span className="top-pill">{getString(curve, "units")}</span>
      </div>
      <svg className="curve-svg" viewBox={`0 0 ${width} ${height}`} role="img">
        <line x1={pad} x2={width - pad} y1={height - pad} y2={height - pad} />
        <line x1={pad} x2={pad} y1={pad} y2={height - pad} />
        <polyline points={polyline} />
        {points.map((point) => {
          const x = pad + ((point.x - xMin) / xSpan) * (width - pad * 2);
          const y = height - pad - ((point.y - yMin) / ySpan) * (height - pad * 2);
          return <circle key={`${point.x}-${point.y}`} cx={x} cy={y} r="4" />;
        })}
      </svg>
      <div className="curve-axis">
        <span>{xMin}</span>
        <span>overall score</span>
        <span>{xMax}</span>
      </div>
    </section>
  );
}

function RelativeYieldView({ payload }: { payload: DashboardPayload }) {
  const relativeYield = getRecord(payload.derived.relative_yield);
  if (!relativeYield) {
    return <AvailabilityPanel title="Relative Yield" availability={payload.sections.relative_yield} />;
  }

  const rows = getNestedRecordArray(relativeYield, "rows");
  const targetLow = getNumber(relativeYield, "target_low_percent") ?? 18;
  const targetHigh = getNumber(relativeYield, "target_high_percent") ?? 22;

  return (
    <section className="panel" aria-labelledby="relative-yield-title">
      <div className="section-heading">
        <div>
          <h2 id="relative-yield-title">{getString(relativeYield, "label", "Relative Yield")}</h2>
          <p>Dummy extraction-yield view for comparing each run against a target espresso window.</p>
        </div>
        <StatusBadge status={payload.sections.relative_yield.status} />
      </div>
      <div className="target-band">
        <span>Target window</span>
        <strong>
          {targetLow.toFixed(1)}-{targetHigh.toFixed(1)}%
        </strong>
      </div>
      <div className="yield-grid">
        {rows.map((row) => {
          const runId = getString(row, "run_id");
          const extraction = getNumber(row, "extraction_yield_percent") ?? 0;
          const sensory = getNumber(row, "sensory_index_percent") ?? 0;
          const inTarget = extraction >= targetLow && extraction <= targetHigh;
          return (
            <div className={inTarget ? "yield-row yield-row--target" : "yield-row"} key={runId}>
              <span>{runId}</span>
              <div className="yield-track">
                <span style={{ width: `${clampPercent((extraction / 26) * 100)}%` }} />
              </div>
              <strong>{extraction.toFixed(1)}%</strong>
              <small>{sensory.toFixed(0)} sensory index</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function RecommendationsView({ payload }: { payload: DashboardPayload }) {
  const recommendations = getRecordArray(payload.derived.recommendations);
  if (recommendations.length === 0) {
    return <AvailabilityPanel title="Recommendations" availability={payload.sections.recommendations} />;
  }

  return (
    <section className="panel" aria-labelledby="recommendations-title">
      <div className="section-heading">
        <div>
          <h2 id="recommendations-title">Dummy Next Runs</h2>
          <p>Illustrative follow-up settings based on the dummy endpoint results.</p>
        </div>
        <StatusBadge status={payload.sections.recommendations.status} />
      </div>
      <div className="recommendation-list">
        {recommendations.map((recommendation) => (
          <RecommendationItem
            key={getString(recommendation, "recommendation_id")}
            recommendation={recommendation}
          />
        ))}
      </div>
    </section>
  );
}

function RecommendationItem({ recommendation }: { recommendation: DataRecord }) {
  const settings = getNestedRecord(recommendation, "factor_settings") ?? {};
  const expected = getNestedRecord(recommendation, "expected_responses") ?? {};

  return (
    <article className="recommendation-item">
      <div>
        <span className="eyebrow">{getString(recommendation, "priority")}</span>
        <h3>{getString(recommendation, "recommendation_id")}</h3>
        <p>{getString(recommendation, "rationale")}</p>
      </div>
      <div className="setting-grid" aria-label="Recommended factor settings">
        {Object.entries(settings).map(([key, value]) => (
          <Fact key={key} label={key} value={formatValue(value)} />
        ))}
      </div>
      <div className="expected-grid" aria-label="Expected dummy responses">
        {Object.entries(expected).map(([key, value]) => (
          <span key={key}>
            <strong>{formatValue(value)}</strong>
            {key}
          </span>
        ))}
      </div>
    </article>
  );
}

function VerificationView({ payload }: { payload: DashboardPayload }) {
  const plan = getRecord(payload.derived.verification_plan);
  if (!plan) {
    return <AvailabilityPanel title="Verification" availability={payload.sections.verification} />;
  }

  const candidate = getNestedRecord(plan, "candidate_run") ?? {};
  const criteria = Array.isArray(plan.acceptance_criteria)
    ? plan.acceptance_criteria.filter((item): item is string => typeof item === "string")
    : [];

  return (
    <section className="panel" aria-labelledby="verification-title">
      <div className="section-heading">
        <div>
          <h2 id="verification-title">Verification Plan</h2>
          <p>Replicate the best dummy setting before treating it as a real latte recipe.</p>
        </div>
        <StatusBadge status={payload.sections.verification.status} />
      </div>
      <div className="verification-layout">
        <section className="analytics-block" aria-label="Candidate settings">
          <div className="section-heading section-heading--compact">
            <h3>{getString(plan, "verification_id")}</h3>
            <span className="top-pill">{formatValue(plan.replicates, 0)} repeats</span>
          </div>
          <div className="setting-grid">
            {Object.entries(candidate).map(([key, value]) => (
              <Fact key={key} label={key} value={formatValue(value)} />
            ))}
          </div>
        </section>
        <section className="analytics-block" aria-label="Acceptance criteria">
          <div className="section-heading section-heading--compact">
            <h3>Acceptance Criteria</h3>
            <span className="top-pill">holdout</span>
          </div>
          <ul className="criteria-list">
            {criteria.map((criterion) => (
              <li key={criterion}>{criterion}</li>
            ))}
          </ul>
        </section>
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

function StatusBadge({ status }: { status: StatusKind }) {
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

function PayloadLoading({ sourceLabel }: { sourceLabel: string }) {
  return (
    <main className="app-shell app-shell--single">
      <section className="panel panel--availability" aria-labelledby="payload-loading-title">
        <p className="eyebrow">Payload source</p>
        <h1 id="payload-loading-title">Loading workbench payload.</h1>
        <p>{sourceLabel}</p>
      </section>
    </main>
  );
}

function PayloadError({ sourceLabel, errors }: { sourceLabel: string; errors: string[] }) {
  return (
    <main className="app-shell app-shell--single">
      <section className="panel panel--error" aria-labelledby="payload-error-title">
        <p className="eyebrow">Payload validation error</p>
        <h1 id="payload-error-title">Payload `{sourceLabel}` cannot be rendered as a dashboard payload.</h1>
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

function EmptyState({ payload, sourceLabel }: { payload: DashboardPayload; sourceLabel: string }) {
  return (
    <main className="app-shell app-shell--single">
      <section className="panel panel--availability" aria-labelledby="empty-title">
        <p className="eyebrow">Payload {sourceLabel || defaultFixtureName}</p>
        <h1 id="empty-title">No study payload is available.</h1>
        <p>Run generate_dashboard_payload from Codex to create one.</p>
        <PayloadFooter payload={payload} />
      </section>
    </main>
  );
}
