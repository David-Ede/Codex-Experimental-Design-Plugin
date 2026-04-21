import { describe, expect, it } from "vitest";
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

  it("rejects malformed payloads before rendering", () => {
    const result = validateDashboardPayload(fixturePayloads.invalid);

    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.errors).toContain("version must be a semantic version string");
      expect(result.errors).toContain("warnings must be an array");
    }
  });
});
