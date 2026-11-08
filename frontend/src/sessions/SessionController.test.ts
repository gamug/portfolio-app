import { describe, expect, it } from "vitest";
import type { Message, Thread, UserMessage } from "@openuidev/react-ui";
import {
  SessionController,
  type ChatClient,
  type PairClient,
  type RelevanceClient,
  type ReportClient,
  type ReportExporter,
  type ReportStreamEvent,
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
  generateImpl: (sessionId: string, signal?: AbortSignal) => AsyncIterable<ReportStreamEvent> =
    async function* () {};

  async getReport(sessionId: string): Promise<SessionReport | null> {
    if (this.fail) throw new Error("report failed");
    return this.reports.get(sessionId) ?? null;
  }

  generateReport(sessionId: string, signal?: AbortSignal): AsyncIterable<ReportStreamEvent> {
    return this.generateImpl(sessionId, signal);
  }
}

class FakeExporter implements ReportExporter {
  calls: Array<{ sessionName: string; report: SessionReport }> = [];
  fail = false;

  async download(sessionName: string, report: SessionReport): Promise<void> {
    if (this.fail) throw new Error("download failed");
    this.calls.push({ sessionName, report });
  }
}

class FakeChats implements ChatClient {
  chunks: string[] = [];
  error: Error | null = null;
  calls: Array<{ question: string; sessionId: string; signal?: AbortSignal }> = [];

  async *streamAnswer(
    question: string,
    sessionId: string,
    signal?: AbortSignal,
  ): AsyncIterable<string> {
    this.calls.push({ question, sessionId, signal });
    for (const chunk of this.chunks) {
      if (signal?.aborted) {
        throw new Error("aborted");
      }
      yield chunk;
    }
    if (this.error !== null) {
      throw this.error;
    }
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

class FakePairs implements PairClient {
  calls: Array<[string, string]> = [];
  fail = false;

  async deletePair(sessionId: string, pairId: string): Promise<void> {
    if (this.fail) throw new Error("pair delete failed");
    this.calls.push([sessionId, pairId]);
  }
}

function report(text: string, incomplete = false): SessionReport {
  return {
    openui_lang: text,
    incomplete,
    created_at: "2026-11-07T00:00:00Z",
    updated_at: "2026-11-07T00:00:00Z",
  };
}

function deferred(): { promise: Promise<void>; resolve: () => void } {
  let resolve: () => void = () => undefined;
  const promise = new Promise<void>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

function makeController() {
  const storage = new FakeStorage();
  const reports = new FakeReports();
  const relevance = new FakeRelevance();
  const pairs = new FakePairs();
  const chats = new FakeChats();
  const exporter = new FakeExporter();
  return {
    storage,
    reports,
    relevance,
    pairs,
    chats,
    exporter,
    controller: new SessionController(storage, reports, relevance, pairs, chats, exporter),
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

describe("SessionController pair deletion", () => {
  it("deletes only the confirmed pair and keeps the report", async () => {
    const { storage, reports, relevance, pairs, controller } = makeController();
    storage.threads = [session("s1")];
    storage.messages.set("s1", [
      message("q1", "user", "First question"),
      message("p1", "assistant", "root = Card([])"),
      message("q2", "user", "Second question"),
      message("p2", "assistant", "root = Stack([])"),
    ]);
    relevance.values.set("p2", false);
    reports.reports.set("s1", report("root = Card([])"));
    await controller.initialize();
    const reportBefore = controller.getSnapshot().report;

    await controller.deletePair("p1", true);

    const state = controller.getSnapshot();
    expect(pairs.calls).toEqual([["s1", "p1"]]);
    expect(state.messages).toEqual([
      message("q2", "user", "Second question"),
      message("p2", "assistant", "root = Stack([])"),
    ]);
    expect(state.relevance).toEqual({ p2: false });
    expect(state.report).toEqual(reportBefore);
  });

  it("does nothing when deletion is declined", async () => {
    const { storage, pairs, controller } = makeController();
    storage.threads = [session("s1")];
    storage.messages.set("s1", [message("p1", "assistant", "root = Card([])")]);
    await controller.initialize();
    const before = controller.getSnapshot();

    await controller.deletePair("p1", false);

    const after = controller.getSnapshot();
    expect(pairs.calls).toEqual([]);
    expect(after.messages).toEqual(before.messages);
    expect(after.report).toEqual(before.report);
    expect(after.relevance).toEqual(before.relevance);
  });

  it("leaves the visible state unchanged when pair deletion fails", async () => {
    const { storage, reports, relevance, pairs, controller } = makeController();
    storage.threads = [session("s1")];
    storage.messages.set("s1", [
      message("q1", "user", "Question"),
      message("p1", "assistant", "root = Card([])"),
    ]);
    relevance.values.set("p1", false);
    reports.reports.set("s1", report("root = Card([])"));
    await controller.initialize();
    const before = controller.getSnapshot();
    pairs.fail = true;

    await controller.deletePair("p1", true);

    const after = controller.getSnapshot();
    expect(after.messages).toEqual(before.messages);
    expect(after.relevance).toEqual(before.relevance);
    expect(after.report).toEqual(before.report);
    expect(after.error).toBeTruthy();
  });

  it("does not delete a pair that is not in the active session", async () => {
    const { storage, pairs, controller } = makeController();
    storage.threads = [session("s1"), session("s2")];
    storage.messages.set("s1", [message("p1", "assistant", "root = Card([])")]);
    await controller.initialize();

    await controller.deletePair("p2", true);

    expect(pairs.calls).toEqual([]);
  });
});

describe("SessionController chat", () => {
  it("streams the raw answer and reloads the stored OpenUI pair", async () => {
    const { storage, chats, relevance, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();
    chats.chunks = ["Raw ", "answer"];
    storage.messages.set("s1", [
      message("q1", "user", "Question"),
      message("p1", "assistant", "root = Card([])"),
    ]);
    relevance.values.set("p1", false);

    await controller.sendQuestion("Question");

    const state = controller.getSnapshot();
    expect(chats.calls[0]).toMatchObject({ question: "Question", sessionId: "s1" });
    expect(state.messages).toEqual([
      message("q1", "user", "Question"),
      message("p1", "assistant", "root = Card([])"),
    ]);
    expect(state.relevance).toEqual({ p1: false });
    expect(state.isSendingChat).toBe(false);
    expect(state.chatStream).toBeNull();
    expect(state.chatError).toBeNull();
  });

  it("shows the localized backend error and does not add the failed question", async () => {
    const { storage, chats, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();
    const before = controller.getSnapshot();
    chats.error = new Error("No se pudo generar la respuesta. Inténtalo de nuevo.");

    await controller.sendQuestion("¿Pregunta?");

    const after = controller.getSnapshot();
    expect(after.messages).toEqual(before.messages);
    expect(after.chatStream).toBeNull();
    expect(after.isSendingChat).toBe(false);
    expect(after.chatError).toBe("No se pudo generar la respuesta. Inténtalo de nuevo.");
  });

  it("does not send a question while a report is being generated", async () => {
    const { storage, reports, chats, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();
    const started = deferred();
    const gate = deferred();
    reports.generateImpl = async function* () {
      yield { type: "progress", stage: "planning" };
      started.resolve();
      await gate.promise;
      yield { type: "done", report: report("root = Card([])") };
    };

    const generation = controller.generateReport();
    await started.promise;
    await controller.sendQuestion("Question");

    expect(chats.calls).toEqual([]);
    gate.resolve();
    await generation;
  });
});

describe("SessionController report generation", () => {
  it("keeps the previous report until the stream completes, then replaces it", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1")];
    reports.reports.set("s1", report("previous"));
    await controller.initialize();
    const reached = deferred();
    const gate = deferred();
    reports.generateImpl = async function* () {
      yield { type: "progress", stage: "planning" };
      yield { type: "progress", stage: "rendering" };
      yield { type: "delta", text: "root = Card([" };
      reached.resolve();
      await gate.promise;
      yield { type: "delta", text: "])" };
      yield { type: "done", report: report("root = Card([])") };
    };

    const generation = controller.generateReport();
    await reached.promise;
    let state = controller.getSnapshot();
    expect(state.isGeneratingReport).toBe(true);
    expect(state.reportProgress).toBe("rendering");
    expect(state.reportStream).toBe("root = Card([");
    expect(state.report?.openui_lang).toBe("previous");

    gate.resolve();
    await generation;

    state = controller.getSnapshot();
    expect(state.isGeneratingReport).toBe(false);
    expect(state.reportProgress).toBeNull();
    expect(state.reportStream).toBe("");
    expect(state.report?.openui_lang).toBe("root = Card([])");
  });

  it("keeps the previous report and re-enables the chat on cancel", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1")];
    reports.reports.set("s1", report("previous"));
    await controller.initialize();
    const started = deferred();
    reports.generateImpl = async function* (_sessionId, signal) {
      yield { type: "progress", stage: "planning" };
      yield { type: "delta", text: "root = Card([" };
      started.resolve();
      await new Promise<void>((_resolve, reject) => {
        signal?.addEventListener("abort", () => reject(new Error("aborted")), { once: true });
      });
    };

    const generation = controller.generateReport();
    await started.promise;
    expect(controller.getSnapshot().isGeneratingReport).toBe(true);

    controller.cancelReportGeneration();
    await generation;

    const state = controller.getSnapshot();
    expect(state.isGeneratingReport).toBe(false);
    expect(state.reportProgress).toBeNull();
    expect(state.reportStream).toBe("");
    expect(state.reportError).toBeNull();
    expect(state.report?.openui_lang).toBe("previous");
  });

  it("reloads the partial report flagged incomplete when the agent fails", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1")];
    reports.reports.set("s1", report("previous"));
    await controller.initialize();
    reports.generateImpl = async function* () {
      yield { type: "progress", stage: "rendering" };
      yield { type: "delta", text: "root = Card([title])" };
      reports.reports.set("s1", report("root = Card([title])", true));
      yield {
        type: "error",
        error: "No se pudo generar el informe. El informe parcial se guardó como incompleto.",
        incomplete: true,
      };
    };

    await controller.generateReport();

    const state = controller.getSnapshot();
    expect(state.isGeneratingReport).toBe(false);
    expect(state.reportStream).toBe("");
    expect(state.report?.openui_lang).toBe("root = Card([title])");
    expect(state.report?.incomplete).toBe(true);
    expect(state.reportError).toContain("informe parcial");
  });

  it("shows the no-history message without replacing the report", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1")];
    reports.reports.set("s1", report("previous"));
    await controller.initialize();
    // eslint-disable-next-line require-yield -- the rejected request is the only outcome.
    reports.generateImpl = async function* () {
      throw new Error("This session has no history. Start the data exploration first.");
    };

    await controller.generateReport();

    const state = controller.getSnapshot();
    expect(state.isGeneratingReport).toBe(false);
    expect(state.report?.openui_lang).toBe("previous");
    expect(state.reportError).toBe(
      "This session has no history. Start the data exploration first.",
    );
  });

  it("shows the nothing-marked message without replacing the report", async () => {
    const { storage, reports, controller } = makeController();
    storage.threads = [session("s1")];
    reports.reports.set("s1", report("previous"));
    await controller.initialize();
    // eslint-disable-next-line require-yield -- the rejected request is the only outcome.
    reports.generateImpl = async function* () {
      throw new Error(
        "No question-answer pair is marked as relevant. Mark at least one pair first.",
      );
    };

    await controller.generateReport();

    const state = controller.getSnapshot();
    expect(state.report?.openui_lang).toBe("previous");
    expect(state.reportError).toContain("Mark at least one pair");
  });
});

describe("SessionController report download", () => {
  it("downloads the active session report with its title", async () => {
    const { storage, reports, exporter, controller } = makeController();
    storage.threads = [session("s1", "Q3 sales")];
    reports.reports.set("s1", report("root = Card([])"));
    await controller.initialize();

    await controller.downloadReport();

    expect(exporter.calls).toEqual([
      { sessionName: "Q3 sales", report: report("root = Card([])") },
    ]);
  });

  it("does nothing when the session has no report", async () => {
    const { storage, exporter, controller } = makeController();
    storage.threads = [session("s1")];
    await controller.initialize();

    await controller.downloadReport();

    expect(exporter.calls).toEqual([]);
    expect(controller.getSnapshot().reportError).toBeNull();
  });

  it("shows an error when the download fails", async () => {
    const { storage, reports, exporter, controller } = makeController();
    storage.threads = [session("s1", "Q3 sales")];
    reports.reports.set("s1", report("root = Card([])"));
    await controller.initialize();
    exporter.fail = true;

    await controller.downloadReport();

    expect(exporter.calls).toEqual([]);
    expect(controller.getSnapshot().reportError).toContain("download");
  });
});
