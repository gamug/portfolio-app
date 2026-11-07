import { describe, expect, it } from "vitest";
import type { Message, Thread, UserMessage } from "@openuidev/react-ui";
import {
  SessionController,
  type RelevanceClient,
  type ReportClient,
  type SessionReport,
  type ThreadStorage,
} from "./SessionController";

function session(id: string, title = id): Thread {
  return { id, title, createdAt: "2026-11-07T00:00:00Z" };
}

function message(id: string, role: "user" | "assistant", content: string): Message {
  return { id, role, content };
}

class FakeStorage implements ThreadStorage {
  threads: Thread[] = [];
  messages = new Map<string, Message[]>();
  deleted: string[] = [];
  created: UserMessage[] = [];
  failCreate = false;
  failDelete = false;
  failUpdate = false;
  failGetMessages = false;
  failList = false;

  async listThreads(): Promise<{ threads: Thread[] }> {
    if (this.failList) throw new Error("list failed");
    return { threads: [...this.threads] };
  }

  async createThread(firstMessage: UserMessage): Promise<Thread> {
    if (this.failCreate) throw new Error("create failed");
    this.created.push(firstMessage);
    const created = session(`new-${this.created.length}`, String(firstMessage.content));
    this.threads = [created, ...this.threads];
    return created;
  }

  async getMessages(threadId: string): Promise<Message[]> {
    if (this.failGetMessages) throw new Error("history failed");
    return this.messages.get(threadId) ?? [];
  }

  async updateThread(thread: Thread): Promise<Thread> {
    if (this.failUpdate) throw new Error("rename failed");
    this.threads = this.threads.map((item) => (item.id === thread.id ? thread : item));
    return thread;
  }

  async deleteThread(id: string): Promise<void> {
    if (this.failDelete) throw new Error("delete failed");
    this.deleted.push(id);
    this.threads = this.threads.filter((item) => item.id !== id);
  }
}

class FakeReports implements ReportClient {
  reports = new Map<string, SessionReport>();
  fail = false;

  async getReport(sessionId: string): Promise<SessionReport | null> {
    if (this.fail) throw new Error("report failed");
    return this.reports.get(sessionId) ?? null;
  }
}

class FakeRelevance implements RelevanceClient {
  values = new Map<string, boolean>();
  calls: Array<[string, string, boolean]> = [];
  failGet = false;
  failSet = false;

  async getRelevance(_sessionId: string, pairId: string): Promise<boolean> {
    if (this.failGet) throw new Error("relevance load failed");
    return this.values.get(pairId) ?? true;
  }

  async setRelevance(sessionId: string, pairId: string, relevant: boolean): Promise<boolean> {
    if (this.failSet) throw new Error("relevance update failed");
    this.calls.push([sessionId, pairId, relevant]);
    this.values.set(pairId, relevant);
    return relevant;
  }
}

function report(text: string): SessionReport {
  return {
    openui_lang: text,
    incomplete: false,
    created_at: "2026-11-07T00:00:00Z",
    updated_at: "2026-11-07T00:00:00Z",
  };
}

function makeController() {
  const storage = new FakeStorage();
  const reports = new FakeReports();
  const relevance = new FakeRelevance();
  return {
    storage,
    reports,
    relevance,
    controller: new SessionController(storage, reports, relevance),
  };
}

describe("SessionController", () => {
  it("loads the first session with its history and report", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1"), session("s2")];
    storage.messages.set("s1", [message("m1", "user", "Question")]);
    reports.reports.set("s1", report("root = Card([])"));

    await controller.initialize();

    const state = controller.getSnapshot();
    expect(state.sessions).toEqual([session("s1"), session("s2")]);
    expect(state.activeSessionId).toBe("s1");
    expect(state.messages).toEqual([message("m1", "user", "Question")]);
    expect(state.report?.openui_lang).toBe("root = Card([])");
  });

  it("creates an empty first session when the backend has none", async () => {
    const { controller } = makeController();
    await controller.initialize();
    const state = controller.getSnapshot();
    expect(state.sessions).toHaveLength(1);
    expect(state.activeSessionId).toBe(state.sessions[0].id);
    expect(state.messages).toEqual([]);
    expect(state.report).toBeNull();
  });

  it("creates a new session and makes it active", async () => {
    const { storage, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();
    await controller.createSession();

    const state = controller.getSnapshot();
    expect(state.sessions[0].title).toBe("New Chat");
    expect(state.activeSessionId).toBe(state.sessions[0].id);
    expect(state.messages).toEqual([]);
    expect(state.report).toBeNull();
  });

  it("selects another session and shows its history and report", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1"), session("s2")];
    storage.messages.set("s1", [message("m1", "user", "First")]);
    storage.messages.set("s2", [message("m2", "user", "Second")]);
    reports.reports.set("s2", report("root = Stack([])"));
    await controller.initialize();

    await controller.selectSession("s2");

    const state = controller.getSnapshot();
    expect(state.activeSessionId).toBe("s2");
    expect(state.messages).toEqual([message("m2", "user", "Second")]);
    expect(state.report?.openui_lang).toBe("root = Stack([])");
  });

  it("renames a session", async () => {
    const { storage, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();

    await controller.renameSession("s1", "Renamed");

    expect(controller.getSnapshot().sessions[0].title).toBe("Renamed");
  });

  it("leaves the visible state unchanged when rename fails", async () => {
    const { storage, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();
    const before = controller.getSnapshot();
    storage.failUpdate = true;

    await controller.renameSession("s1", "Renamed");

    const after = controller.getSnapshot();
    expect(after.sessions).toEqual(before.sessions);
    expect(after.activeSessionId).toBe(before.activeSessionId);
    expect(after.error).toBeTruthy();
  });

  it("does not delete without explicit confirmation", async () => {
    const { storage, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();

    await controller.deleteSession("s1", false);

    expect(storage.deleted).toEqual([]);
    expect(controller.getSnapshot().sessions).toHaveLength(1);
  });

  it("creates and selects a new empty session after deleting the active one", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1")];
    storage.messages.set("s1", [message("m1", "user", "Old")]);
    reports.reports.set("s1", report("root = Card([])"));
    await controller.initialize();

    await controller.deleteSession("s1", true);

    const state = controller.getSnapshot();
    expect(storage.deleted).toEqual(["s1"]);
    expect(state.sessions).toHaveLength(1);
    expect(state.sessions[0].id).toBe("new-1");
    expect(state.activeSessionId).toBe("new-1");
    expect(state.messages).toEqual([]);
    expect(state.report).toBeNull();
  });

  it("leaves the visible state unchanged when delete fails", async () => {
    const { storage, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();
    const before = controller.getSnapshot();
    storage.failDelete = true;

    await controller.deleteSession("s1", true);

    const after = controller.getSnapshot();
    expect(after.sessions).toEqual(before.sessions);
    expect(after.activeSessionId).toBe(before.activeSessionId);
    expect(after.messages).toEqual(before.messages);
    expect(after.report).toEqual(before.report);
    expect(after.error).toBeTruthy();
  });

  it("leaves the visible state unchanged when create fails", async () => {
    const { storage, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();
    const before = controller.getSnapshot();
    storage.failCreate = true;

    await controller.createSession();

    const after = controller.getSnapshot();
    expect(after.sessions).toEqual(before.sessions);
    expect(after.activeSessionId).toBe(before.activeSessionId);
    expect(after.error).toBeTruthy();
  });

  it("leaves the visible state unchanged when selecting a session fails", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1"), session("s2")];
    storage.messages.set("s1", [message("m1", "user", "First")]);
    reports.reports.set("s1", report("root = Card([])"));
    await controller.initialize();
    const before = controller.getSnapshot();
    storage.failGetMessages = true;

    await controller.selectSession("s2");

    const after = controller.getSnapshot();
    expect(after.activeSessionId).toBe(before.activeSessionId);
    expect(after.messages).toEqual(before.messages);
    expect(after.report).toEqual(before.report);
    expect(after.error).toBeTruthy();
  });
});

describe("SessionController relevance", () => {
  it("loads the stored relevance state for each assistant message", async () => {
    const { storage, relevance, controller } = makeController();
    storage.threads = [session("s1")];
    storage.messages.set("s1", [
      message("q1", "user", "Question"),
      message("p1", "assistant", "root = Card([])"),
    ]);
    relevance.values.set("p1", false);

    await controller.initialize();

    expect(controller.getSnapshot().relevance).toEqual({ p1: false });
  });

  it("toggles a pair and persists the new state", async () => {
    const { storage, relevance, controller } = makeController();
    storage.threads = [session("s1")];
    storage.messages.set("s1", [message("p1", "assistant", "root = Card([])")]);
    await controller.initialize();

    await controller.toggleRelevance("p1");

    expect(relevance.calls).toEqual([["s1", "p1", false]]);
    expect(controller.getSnapshot().relevance["p1"]).toBe(false);
  });

  it("leaves the visible relevance unchanged when the update fails", async () => {
    const { storage, relevance, controller } = makeController();
    storage.threads = [session("s1")];
    storage.messages.set("s1", [message("p1", "assistant", "root = Card([])")]);
    await controller.initialize();
    const before = controller.getSnapshot().relevance;
    relevance.failSet = true;

    await controller.toggleRelevance("p1");

    const after = controller.getSnapshot();
    expect(after.relevance).toEqual(before);
    expect(after.error).toBeTruthy();
  });

  it("loads relevance again when switching sessions", async () => {
    const { storage, relevance, controller } = makeController();
    storage.threads = [session("s1"), session("s2")];
    storage.messages.set("s1", [message("p1", "assistant", "root = Card([])")]);
    storage.messages.set("s2", [message("p2", "assistant", "root = Stack([])")]);
    relevance.values.set("p2", false);
    await controller.initialize();

    await controller.selectSession("s2");

    expect(controller.getSnapshot().relevance).toEqual({ p2: false });
  });
});
