import { describe, expect, it } from "vitest";
import { AgentAdapterError } from "../src/main/agents/adapter.js";
import { FakeAgentAdapter } from "../src/main/agents/fake-adapter.js";

describe("FakeAgentAdapter", () => {
  it("reports available by default", async () => {
    const adapter = new FakeAgentAdapter();
    const result = await adapter.detect();
    expect(result.available).toBe(true);
    expect(result.version).toBe("0.0.0-fake");
    expect(adapter.getStatus()).toBe("idle");
  });

  it("can be configured as unavailable", async () => {
    const adapter = new FakeAgentAdapter({ available: false });
    const result = await adapter.detect();
    expect(result.available).toBe(false);
    expect(result.detail).toMatch(/unavailable/i);
  });

  it("starts, accepts send, and stops without spawning processes", async () => {
    const adapter = new FakeAgentAdapter({ id: "fake-a" });
    await adapter.start({
      workspacePath: "/tmp/repo",
      taskPrompt: "fix a typo",
    });
    expect(adapter.getStatus()).toBe("running");
    expect(adapter.getLastStartOptions()?.taskPrompt).toBe("fix a typo");

    await adapter.send("continue");
    expect(adapter.getInbox()).toEqual(["continue"]);

    await adapter.stop();
    expect(adapter.getStatus()).toBe("stopped");
  });

  it("rejects start while already running", async () => {
    const adapter = new FakeAgentAdapter();
    await adapter.start({ workspacePath: "/repo", taskPrompt: "task" });
    await expect(
      adapter.start({ workspacePath: "/repo", taskPrompt: "again" }),
    ).rejects.toBeInstanceOf(AgentAdapterError);
  });

  it("rejects send when not running", async () => {
    const adapter = new FakeAgentAdapter();
    await expect(adapter.send("nope")).rejects.toMatchObject({
      code: "AGENT_INVALID_STATE",
    });
  });
});
