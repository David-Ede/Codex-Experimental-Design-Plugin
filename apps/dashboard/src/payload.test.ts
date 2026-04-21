import { describe, expect, it } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { WorkbenchView } from "./App";
import { fixturePayloads, validateDashboardPayload } from "./payload";

describe("dashboard payload validation", () => {
  it("accepts the phase 0 design-only fixture", () => {
    const result = validateDashboardPayload(fixturePayloads.phase0);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.study?.study_id).toBe("minimal_doe");
      expect(result.data.sections.economics.status).toBe("unavailable_missing_input");
    }
  });

  it("accepts the perfect latte dummy analytics fixture", () => {
    const result = validateDashboardPayload(fixturePayloads.latte);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.study?.study_id).toBe("perfect_latte_doe");
      expect(result.data.sections.effects.status).toBe("available");
      expect(result.data.sections.economics.status).toBe("unavailable_missing_input");
    }
  });

  it("accepts the empty payload state fixture", () => {
    const result = validateDashboardPayload(fixturePayloads.empty);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.study).toBeNull();
    }
  });

  it("accepts the workbench candidate-design fixture", () => {
    const result = validateDashboardPayload(fixturePayloads.workbench);

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.data.workbench?.candidate_design_sets[0].candidates).toHaveLength(3);
      expect(result.data.workbench?.contextual_ai_panels[0].source_refs.length).toBeGreaterThan(0);
    }
  });

  it("renders the workbench payload without recomputing scientific state", () => {
    const result = validateDashboardPayload(fixturePayloads.workbench);

    expect(result.ok).toBe(true);
    if (result.ok && result.data.workbench) {
      const html = renderToString(
        React.createElement(WorkbenchView, { payload: result.data, workbench: result.data.workbench })
      );

      expect(html).toContain("Candidate Design Comparison");
      expect(html).toContain("Side-by-side comparison");
      expect(html).toContain("Why this design?");
      expect(html).toContain("outputs/studies/ivt_strategy_studio");
    }
  });

  it("rejects workbench explanation panels without source refs", () => {
    const payload = JSON.parse(JSON.stringify(fixturePayloads.workbench));
    delete payload.workbench.contextual_ai_panels[0].source_refs;

    const result = validateDashboardPayload(payload);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.errors).toContain(
        "workbench.contextual_ai_panels[0].source_refs must contain at least one source ref"
      );
    }
  });

  it("rejects unsupported candidates that are presented as successful", () => {
    const payload = JSON.parse(JSON.stringify(fixturePayloads.workbench));
    const candidate = payload.workbench.candidate_design_sets[0].candidates[0];
    candidate.status = "unsupported";
    candidate.recommendation_label = "Recommended";
    candidate.ranking_score = 0.9;
    candidate.capabilities.main_effects = "supported";

    const result = validateDashboardPayload(payload);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.errors).toContain(
        "workbench.candidate_design_sets[0].candidates[0].ranking_score must be null for unsupported"
      );
      expect(result.errors).toContain(
        "workbench.candidate_design_sets[0].candidates[0] cannot present unsupported as recommended"
      );
      expect(result.errors).toContain(
        "workbench.candidate_design_sets[0].candidates[0] cannot show supported capabilities when unsupported"
      );
    }
  });

  it("rejects malformed payloads before rendering", () => {
    const result = validateDashboardPayload(fixturePayloads.invalid);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.errors).toContain("version must be a semantic version string");
      expect(result.errors).toContain("warnings must be an array");
    }
  });
});
