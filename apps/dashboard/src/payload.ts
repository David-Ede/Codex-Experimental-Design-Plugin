import emptyPayloadState from "../../../fixtures/dashboard/empty_payload_state.json";
import payloadValidationError from "../../../fixtures/dashboard/payload_validation_error.json";
import perfectLattePayload from "../../../fixtures/dashboard/perfect_latte_dummy_payload.json";
import phase0DesignOnlyPayload from "../../../fixtures/dashboard/phase0_design_only_payload.json";
import workbenchCandidateDesignsPayload from "../../../fixtures/dashboard/workbench_candidate_designs_payload.json";
import minimalStudyPayload from "../../../fixtures/studies/minimal_doe/dashboard_payload.json";

export type AvailabilityStatus =
  | "available"
  | "unavailable_missing_input"
  | "unavailable_not_run"
  | "unavailable_failed_validation"
  | "unavailable_unsupported";

export type Availability = {
  status: AvailabilityStatus;
  reason: string | null;
  required_inputs: string[];
  source_artifacts: string[];
};

export type Warning = {
  code: string;
  severity: "info" | "warning" | "blocking";
  message: string;
  field?: string | null;
  details?: Record<string, unknown>;
};

export type Factor = {
  name: string;
  display_name: string;
  units: string;
  kind: string;
  low?: number | null;
  high?: number | null;
};

export type ResponseSpec = {
  name: string;
  display_name: string;
  units: string;
  goal: string;
};

export type StudySummary = {
  study_id: string;
  title: string;
  domain_template: string;
  status: string;
  active_design_id?: string | null;
  active_fit_id?: string | null;
  active_construct_id?: string | null;
};

export type DesignRow = Record<string, string | number | boolean | null>;

export type DesignSummary = {
  design_id: string;
  design_type: string;
  status: string;
  matrix?: DesignRow[];
};

export type CapabilitySupport =
  | "supported"
  | "partially_supported"
  | "unsupported"
  | "unknown"
  | "not_applicable";

export type CandidateStatus =
  | "recommended"
  | "available"
  | "available_with_warnings"
  | "not_recommended"
  | "infeasible"
  | "unsupported"
  | "failed_validation"
  | "stale";

export type LearnabilityItem = {
  claim: string;
  label: string;
  support: CapabilitySupport;
  reason_code: string | null;
  source_ref: string;
};

export type CandidateDesign = {
  candidate_design_id: string;
  design_id: string | null;
  design_family: string;
  status: CandidateStatus;
  run_count: number | null;
  recommendation_label: string;
  ranking_score: number | null;
  best_for?: string[];
  capabilities: Record<string, CapabilitySupport>;
  diagnostics: {
    model_matrix_rank: number | null;
    n_model_columns: number | null;
    condition_number: number | null;
    estimable_term_fraction: number | null;
    [key: string]: unknown;
  };
  tradeoffs: string[];
  unavailable_reasons: string[];
  learnability: {
    learnable: LearnabilityItem[];
    not_learnable: LearnabilityItem[];
  };
  source_artifacts: Array<{
    artifact_type: string;
    path: string;
    artifact_hash: string;
  }>;
  warnings: Warning[];
};

export type CandidateDesignSet = {
  candidate_set_id: string;
  study_id: string;
  source_snapshot_id: string | null;
  recommendation_mode: string;
  generated_at: string;
  generator_tool: string;
  input_hash: string;
  candidates: CandidateDesign[];
  ranking_summary: {
    preferred_candidate_design_id: string | null;
    ranking_basis: string;
    weights: Record<string, number>;
  };
  warnings: Warning[];
};

export type DesignComparison = {
  comparison_id: string;
  candidate_set_id: string;
  selected_candidate_design_ids: string[];
  active_metrics: string[];
  preferred_candidate_design_id: string | null;
  user_selected_candidate_design_id: string | null;
  decision_notes: string | null;
  generated_at: string;
};

export type RunPlanCommit = {
  run_plan_id: string;
  source_candidate_design_id: string;
  source_comparison_id: string;
  committed_at: string;
  run_count: number;
  run_matrix_path: string;
  protocol_notes_path: string;
  source_artifacts: string[];
};

export type StudySnapshot = {
  snapshot_id: string;
  label: string;
  created_at: string;
  study_state_hash: string;
  setup_hash: string;
  active_candidate_set_id: string | null;
  active_comparison_id: string | null;
  committed_run_plan_id: string | null;
  notes: string | null;
};

export type ContextualAIPanel = {
  panel_id: string;
  object_type: string;
  object_id: string;
  title: string;
  summary: string;
  best_for: string[];
  tradeoffs: string[];
  watch_out_for: string[];
  source_refs: string[];
};

export type WorkbenchPayload = {
  mode: string;
  study_stage: string;
  recommendation_mode: string;
  candidate_design_sets: CandidateDesignSet[];
  active_comparison: DesignComparison | null;
  committed_run_plan: RunPlanCommit | null;
  snapshots: StudySnapshot[];
  stale_state: {
    is_stale: boolean;
    stale_due_to: string[];
    affected_objects: Array<{
      object_type: string;
      object_id: string;
    }>;
  };
  contextual_ai_panels: ContextualAIPanel[];
};

export type DashboardPayload = {
  version: string;
  payload_metadata: {
    payload_id: string;
    study_id: string | null;
    run_id: string;
    generated_at: string;
    schema_version: string;
    payload_hash: string;
    source_artifacts: Array<{
      artifact_type: string;
      path: string;
      artifact_hash: string;
    }>;
  };
  study: StudySummary | null;
  factor_space: { factors?: Factor[] } | null;
  responses: ResponseSpec[];
  constructs: unknown[];
  designs: DesignSummary[];
  observations: Record<string, unknown>;
  models: unknown[];
  derived: Record<string, unknown>;
  dashboard_state: Record<string, unknown>;
  sections: Record<string, Availability>;
  warnings: Warning[];
  audit: Record<string, unknown>;
  workbench?: WorkbenchPayload | null;
};

export type PayloadValidationResult =
  | { ok: true; data: DashboardPayload; errors: [] }
  | { ok: false; data: null; errors: string[] };

export const fixturePayloads = {
  empty: emptyPayloadState,
  invalid: payloadValidationError,
  latte: perfectLattePayload,
  minimal: minimalStudyPayload,
  phase0: phase0DesignOnlyPayload,
  workbench: workbenchCandidateDesignsPayload
} as const;

export type FixtureName = keyof typeof fixturePayloads;

export const defaultFixtureName: FixtureName = "phase0";

const semverPattern = /^\d+\.\d+\.\d+$/;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasString(record: Record<string, unknown>, key: string): boolean {
  return typeof record[key] === "string" && (record[key] as string).length > 0;
}

function hasArray(record: Record<string, unknown>, key: string): boolean {
  return Array.isArray(record[key]);
}

function isNonEmptyStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.length > 0 && value.every((item) => typeof item === "string" && item.length > 0);
}

function validateWorkbenchSection(value: unknown, errors: string[]) {
  if (value === undefined || value === null) {
    return;
  }
  if (!isRecord(value)) {
    errors.push("workbench must be an object or null");
    return;
  }

  const candidateSets = Array.isArray(value.candidate_design_sets) ? value.candidate_design_sets : [];
  candidateSets.forEach((candidateSet, setIndex) => {
    if (!isRecord(candidateSet)) {
      errors.push(`workbench.candidate_design_sets[${setIndex}] must be an object`);
      return;
    }
    const candidates = Array.isArray(candidateSet.candidates) ? candidateSet.candidates : [];
    candidates.forEach((candidate, candidateIndex) => {
      if (!isRecord(candidate)) {
        errors.push(
          `workbench.candidate_design_sets[${setIndex}].candidates[${candidateIndex}] must be an object`
        );
        return;
      }
      if (!Array.isArray(candidate.source_artifacts) || candidate.source_artifacts.length === 0) {
        errors.push(
          `workbench.candidate_design_sets[${setIndex}].candidates[${candidateIndex}].source_artifacts must contain at least one source artifact`
        );
      }
      const status = candidate.status;
      if (status === "unsupported" || status === "infeasible" || status === "failed_validation") {
        if (candidate.ranking_score !== null) {
          errors.push(
            `workbench.candidate_design_sets[${setIndex}].candidates[${candidateIndex}].ranking_score must be null for ${status}`
          );
        }
        const label = typeof candidate.recommendation_label === "string" ? candidate.recommendation_label.toLowerCase() : "";
        if (label.includes("recommended")) {
          errors.push(
            `workbench.candidate_design_sets[${setIndex}].candidates[${candidateIndex}] cannot present ${status} as recommended`
          );
        }
        const capabilities = isRecord(candidate.capabilities) ? Object.values(candidate.capabilities) : [];
        if (status === "unsupported" && capabilities.includes("supported")) {
          errors.push(
            `workbench.candidate_design_sets[${setIndex}].candidates[${candidateIndex}] cannot show supported capabilities when unsupported`
          );
        }
      }
    });
  });

  const panels = Array.isArray(value.contextual_ai_panels) ? value.contextual_ai_panels : [];
  panels.forEach((panel, index) => {
    if (!isRecord(panel)) {
      errors.push(`workbench.contextual_ai_panels[${index}] must be an object`);
      return;
    }
    if (!isNonEmptyStringArray(panel.source_refs)) {
      errors.push(`workbench.contextual_ai_panels[${index}].source_refs must contain at least one source ref`);
    }
  });

  if (value.committed_run_plan !== null && value.committed_run_plan !== undefined) {
    if (!isRecord(value.committed_run_plan)) {
      errors.push("workbench.committed_run_plan must be an object or null");
    } else {
      for (const key of ["source_candidate_design_id", "source_comparison_id", "run_matrix_path"]) {
        if (!hasString(value.committed_run_plan, key)) {
          errors.push(`workbench.committed_run_plan.${key} must be a string`);
        }
      }
    }
  }
}

export function validateDashboardPayload(value: unknown): PayloadValidationResult {
  const errors: string[] = [];

  if (!isRecord(value)) {
    return { ok: false, data: null, errors: ["payload must be an object"] };
  }

  if (!hasString(value, "version") || !semverPattern.test(value.version as string)) {
    errors.push("version must be a semantic version string");
  }

  if (!isRecord(value.payload_metadata)) {
    errors.push("payload_metadata must be an object");
  } else {
    for (const key of ["payload_id", "run_id", "generated_at", "schema_version", "payload_hash"]) {
      if (!hasString(value.payload_metadata, key)) {
        errors.push(`payload_metadata.${key} must be a string`);
      }
    }
    if (!Array.isArray(value.payload_metadata.source_artifacts)) {
      errors.push("payload_metadata.source_artifacts must be an array");
    }
  }

  if (value.study !== null) {
    if (!isRecord(value.study)) {
      errors.push("study must be an object or null");
    } else {
      for (const key of ["study_id", "title", "status", "domain_template"]) {
        if (!hasString(value.study, key)) {
          errors.push(`study.${key} must be a string`);
        }
      }
    }
  }

  for (const key of ["responses", "constructs", "designs", "models", "warnings"]) {
    if (!hasArray(value, key)) {
      errors.push(`${key} must be an array`);
    }
  }

  for (const key of ["observations", "derived", "dashboard_state", "sections", "audit"]) {
    if (!isRecord(value[key])) {
      errors.push(`${key} must be an object`);
    }
  }

  if (value.factor_space !== null && !isRecord(value.factor_space)) {
    errors.push("factor_space must be an object or null");
  }

  validateWorkbenchSection(value.workbench, errors);

  return errors.length === 0
    ? { ok: true, data: value as DashboardPayload, errors: [] }
    : { ok: false, data: null, errors };
}

export function getFixtureNameFromLocation(search: string): FixtureName {
  const requested = new URLSearchParams(search).get("fixture");
  if (requested && requested in fixturePayloads) {
    return requested as FixtureName;
  }
  return defaultFixtureName;
}

export function getPayloadUrlFromLocation(search: string): string | null {
  const requested = new URLSearchParams(search).get("payloadUrl");
  return requested && requested.length > 0 ? requested : null;
}
