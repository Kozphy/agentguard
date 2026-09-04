import { describe, expect, it } from "vitest";
import { AgentAdapterError } from "../src/main/agents/adapter.js";
import { FakeAgentAdapter } from "../src/main/agents/fake-adapter.js";
import { AgentRegistry } from "../src/main/agents/registry.js";

describe("AgentRegistry", () => {
  it("defaults to FakeAgentAdapter", () => {
    const registry = new AgentRegistry();
    const listed = registry.list();
    expect(listed).toHaveLength(1);
    expect(listed[0]?.id).toBe("fake");
    expect(listed[0]?.status).toBe("idle");
  });

  it("registers and retrieves adapters by id", () => {
    const registry = new AgentRegistry([]);
    registry.register(new FakeAgentAdapter({ id: "a", displayName: "A" }));
    registry.register(new FakeAgentAdapter({ id: "b", displayName: "B" }));
    expect(registry.list().map((item) => item.id).sort()).toEqual(["a", "b"]);
    expect(registry.get("a").displayName).toBe("A");
  });

  it("throws AGENT_NOT_FOUND for unknown ids", () => {
    const registry = new AgentRegistry([]);
    expect(() => registry.get("missing")).toThrow(AgentAdapterError);
    try {
      registry.get("missing");
    } catch (error) {
      expect(error).toMatchObject({ code: "AGENT_NOT_FOUND" });
    }
  });
});
