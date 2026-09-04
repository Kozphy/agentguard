import { describe, expect, it } from "vitest";
import { err, ok } from "../src/main/ipc/result.js";

describe("IPC Result helpers", () => {
  it("builds ok and err envelopes", () => {
    expect(ok({ path: "/repo", isGitRepository: true })).toEqual({
      ok: true,
      value: { path: "/repo", isGitRepository: true },
    });
    expect(err("INTERNAL", "boom")).toEqual({
      ok: false,
      error: { code: "INTERNAL", message: "boom" },
    });
  });
});
