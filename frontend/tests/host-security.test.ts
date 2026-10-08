import { describe, expect, it } from "vitest";

import { isAllowedHost } from "@/lib/host-security";

describe("host validation", () => {
  it("allows configured hosts with a port", () => {
    expect(isAllowedHost("frontend.test:3000", "localhost,frontend.test")).toBe(
      true,
    );
  });

  it("rejects missing, empty, and unconfigured hosts", () => {
    expect(isAllowedHost(null, "frontend.test")).toBe(false);
    expect(isAllowedHost("frontend.test", "")).toBe(false);
    expect(isAllowedHost("attacker.test", "frontend.test")).toBe(false);
  });
});
