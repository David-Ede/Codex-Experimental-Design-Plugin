import emptyPayloadState from "../../../fixtures/dashboard/empty_payload_state.json";
import payloadValidationError from "../../../fixtures/dashboard/payload_validation_error.json";
import perfectLattePayload from "../../../fixtures/dashboard/perfect_latte_dummy_payload.json";
import phase0DesignOnlyPayload from "../../../fixtures/dashboard/phase0_design_only_payload.json";
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
};

export type PayloadValidationResult =
  | { ok: true; data: DashboardPayload; errors: [] }
  | { ok: false; data: null; errors: string[] };

export const fixturePayloads = {
  empty: emptyPayloadState,
  invalid: payloadValidationError,
  latte: perfectLattePayload,
  minimal: minimalStudyPayload,
  phase0: phase0DesignOnlyPayload
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
