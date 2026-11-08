import type { ChatStorage, Message, Thread, UserMessage } from "@openuidev/react-ui";

export type ThreadStorage = ChatStorage["thread"];

export type SessionReport = {
  openui_lang: string;
  incomplete: boolean;
  created_at: string;
  updated_at: string;
};

export type ReportStage = "planning" | "rendering";

export type ReportStreamEvent =
  | { type: "progress"; stage: ReportStage }
  | { type: "delta"; text: string }
  | { type: "done"; report: SessionReport }
  | { type: "error"; error: string; incomplete: boolean };

export interface ReportClient {
  getReport(sessionId: string): Promise<SessionReport | null>;
  generateReport(sessionId: string, signal?: AbortSignal): AsyncIterable<ReportStreamEvent>;
}

export interface RelevanceClient {
  getRelevance(sessionId: string, pairId: string): Promise<boolean>;
  setRelevance(sessionId: string, pairId: string, relevant: boolean): Promise<boolean>;
}

export interface PairClient {
  deletePair(sessionId: string, pairId: string): Promise<void>;
}

export interface ChatClient {
  streamAnswer(question: string, sessionId: string, signal?: AbortSignal): AsyncIterable<string>;
}

export interface ReportExporter {
  download(sessionName: string, report: SessionReport): Promise<void>;
}

export interface EraseClient {
  eraseHistory(sessionId: string): Promise<void>;
  eraseReport(sessionId: string): Promise<void>;
}

export type ChatStream = {
  question: string;
  answer: string;
};

export type SessionState = {
  sessions: Thread[];
  activeSessionId: string | null;
  messages: Message[];
  report: SessionReport | null;
  relevance: Record<string, boolean>;
  isLoading: boolean;
  error: string | null;
  isSendingChat: boolean;
  chatStream: ChatStream | null;
  chatError: string | null;
  isGeneratingReport: boolean;
  reportProgress: ReportStage | null;
  reportStream: string;
  reportError: string | null;
  downloadNotice: string | null;
};

const LOAD_ERROR = "Could not load sessions. Please try again.";
const CREATE_ERROR = "Could not create a session. Please try again.";
const RENAME_ERROR = "Could not rename the session. Please try again.";
const DELETE_ERROR = "Could not delete the session. Please try again.";
const SELECT_ERROR = "Could not load the session. Please try again.";
const RELEVANCE_ERROR = "Could not update the relevance. Please try again.";
const PAIR_DELETE_ERROR = "Could not delete the question-answer pair. Please try again.";
const CHAT_ERROR = "Could not send the question. Please try again.";
const REPORT_ERROR = "Could not generate the report. Please try again.";
const REPORT_STREAM_ERROR = "The report stream ended unexpectedly. Please try again.";
const DOWNLOAD_ERROR = "Could not download the report. Please try again.";
const ERASE_HISTORY_ERROR = "Could not erase the history. Please try again.";
const ERASE_REPORT_ERROR = "Could not erase the report. Please try again.";
export const NO_REPORT_MESSAGE = "No report is stored yet. Generate a report first.";

function newUserMessage(): UserMessage {
  const id =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `session-${Date.now()}`;
  return { id, role: "user", content: "New Chat" };
}

function idleStreamingState(): Pick<
  SessionState,
  | "isSendingChat"
  | "chatStream"
  | "chatError"
  | "isGeneratingReport"
  | "reportProgress"
  | "reportStream"
  | "reportError"
  | "downloadNotice"
> {
  return {
    isSendingChat: false,
    chatStream: null,
    chatError: null,
    isGeneratingReport: false,
    reportProgress: null,
    reportStream: "",
    reportError: null,
    downloadNotice: null,
  };
}

function errorText(error: unknown, fallback: string): string {
  return error instanceof Error && error.message.trim().length > 0 ? error.message : fallback;
}

export class SessionController {
  private state: SessionState = {
    sessions: [],
    activeSessionId: null,
    messages: [],
    report: null,
    relevance: {},
    isLoading: false,
    error: null,
    ...idleStreamingState(),
  };
  private readonly listeners = new Set<() => void>();
  private chatAbort: AbortController | null = null;
  private reportAbort: AbortController | null = null;

  constructor(
    private readonly storage: ThreadStorage,
    private readonly reports: ReportClient,
    private readonly relevance: RelevanceClient,
    private readonly pairs: PairClient,
    private readonly chats: ChatClient,
    private readonly exporter: ReportExporter,
    private readonly eraser: EraseClient,
  ) {}

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getSnapshot = (): SessionState => this.state;

  private setState(next: Partial<SessionState>): void {
    this.state = { ...this.state, ...next };
    for (const listener of this.listeners) {
      listener();
    }
  }

  private abortStreams(): void {
    this.chatAbort?.abort();
    this.reportAbort?.abort();
    this.chatAbort = null;
    this.reportAbort = null;
    this.setState({ ...idleStreamingState() });
  }

  async initialize(): Promise<void> {
    this.abortStreams();
    this.setState({ ...idleStreamingState(), isLoading: true, error: null });
    try {
      const { threads = [] } = await this.storage.listThreads(undefined);
      if (threads.length === 0) {
        const session = await this.storage.createThread(newUserMessage());
        this.setState({
          sessions: [session],
          activeSessionId: session.id,
          messages: [],
          report: null,
          relevance: {},
          isLoading: false,
        });
        return;
      }
      this.setState({ sessions: threads, activeSessionId: threads[0].id });
      await this.loadSession(threads[0].id);
    } catch {
      this.setState({ isLoading: false, error: LOAD_ERROR });
    }
  }

  async createSession(): Promise<void> {
    this.abortStreams();
    this.setState({ ...idleStreamingState(), isLoading: true, error: null });
    try {
      const session = await this.storage.createThread(newUserMessage());
      this.setState({
        sessions: [session, ...this.state.sessions],
        activeSessionId: session.id,
        messages: [],
        report: null,
        relevance: {},
        isLoading: false,
      });
    } catch {
      this.setState({ isLoading: false, error: CREATE_ERROR });
    }
  }

  async selectSession(sessionId: string): Promise<void> {
    if (!this.state.sessions.some((session) => session.id === sessionId)) {
      return;
    }
    await this.loadSession(sessionId);
  }

  private async loadSession(sessionId: string): Promise<void> {
    this.abortStreams();
    this.setState({ ...idleStreamingState(), isLoading: true, error: null });
    try {
      const [messages, report] = await Promise.all([
        this.storage.getMessages(sessionId),
        this.reports.getReport(sessionId),
      ]);
      const pairIds = messages
        .filter((message) => message.role === "assistant")
        .map((message) => message.id);
      const relevanceEntries = await Promise.all(
        pairIds.map(async (pairId) => {
          const relevant = await this.relevance.getRelevance(sessionId, pairId);
          return [pairId, relevant] as const;
        }),
      );
      this.setState({
        activeSessionId: sessionId,
        messages,
        report,
        relevance: Object.fromEntries(relevanceEntries),
        isLoading: false,
      });
    } catch {
      this.setState({ isLoading: false, error: SELECT_ERROR });
    }
  }

  async renameSession(sessionId: string, title: string): Promise<void> {
    const session = this.state.sessions.find((item) => item.id === sessionId);
    if (session === undefined || title.trim().length === 0) {
      return;
    }
    this.setState({ isLoading: true, error: null });
    try {
      const updated = await this.storage.updateThread({ ...session, title: title.trim() });
      this.setState({
        sessions: this.state.sessions.map((item) => (item.id === updated.id ? updated : item)),
        isLoading: false,
      });
    } catch {
      this.setState({ isLoading: false, error: RENAME_ERROR });
    }
  }

  async deleteSession(sessionId: string, confirmed: boolean): Promise<void> {
    if (!confirmed) {
      return;
    }
    const session = this.state.sessions.find((item) => item.id === sessionId);
    if (session === undefined) {
      return;
    }
    const deletingActive = this.state.activeSessionId === sessionId;
    if (deletingActive) {
      this.abortStreams();
    }
    this.setState({ isLoading: true, error: null });
    let replacement: Thread | null = null;
    try {
      if (deletingActive) {
        replacement = await this.storage.createThread(newUserMessage());
      }
      await this.storage.deleteThread(sessionId);
    } catch {
      if (replacement !== null) {
        try {
          await this.storage.deleteThread(replacement.id);
        } catch {
          // Keep the original visible state; the orphan cleanup is best effort.
        }
      }
      this.setState({ isLoading: false, error: DELETE_ERROR });
      return;
    }

    const remaining = this.state.sessions.filter((item) => item.id !== sessionId);
    if (deletingActive && replacement !== null) {
      this.setState({
        ...idleStreamingState(),
        sessions: [replacement, ...remaining],
        activeSessionId: replacement.id,
        messages: [],
        report: null,
        relevance: {},
        isLoading: false,
      });
      return;
    }
    this.setState({ sessions: remaining, isLoading: false });
  }

  private withoutPair(messages: Message[], pairId: string): Message[] {
    const index = messages.findIndex(
      (message) => message.id === pairId && message.role === "assistant",
    );
    if (index === -1) {
      return messages.filter((message) => message.id !== pairId);
    }
    const previousIsQuestion = index > 0 && messages[index - 1]?.role === "user";
    return messages.filter(
      (_, messageIndex) =>
        messageIndex !== index && (!previousIsQuestion || messageIndex !== index - 1),
    );
  }

  async deletePair(pairId: string, confirmed: boolean): Promise<void> {
    if (!confirmed || this.state.isGeneratingReport || this.state.isSendingChat) {
      return;
    }
    const sessionId = this.state.activeSessionId;
    if (sessionId === null) {
      return;
    }
    const exists = this.state.messages.some(
      (message) => message.id === pairId && message.role === "assistant",
    );
    if (!exists) {
      return;
    }
    this.setState({ isLoading: true, error: null });
    try {
      await this.pairs.deletePair(sessionId, pairId);
      const relevance = { ...this.state.relevance };
      delete relevance[pairId];
      this.setState({
        messages: this.withoutPair(this.state.messages, pairId),
        relevance,
        isLoading: false,
      });
    } catch {
      this.setState({ isLoading: false, error: PAIR_DELETE_ERROR });
    }
  }

  async toggleRelevance(pairId: string): Promise<void> {
    if (this.state.isGeneratingReport || this.state.isSendingChat) {
      return;
    }
    const sessionId = this.state.activeSessionId;
    if (sessionId === null) {
      return;
    }
    const current = this.state.relevance[pairId] ?? true;
    this.setState({ isLoading: true, error: null });
    try {
      const relevant = await this.relevance.setRelevance(sessionId, pairId, !current);
      this.setState({
        relevance: { ...this.state.relevance, [pairId]: relevant },
        isLoading: false,
      });
    } catch {
      this.setState({ isLoading: false, error: RELEVANCE_ERROR });
    }
  }

  async sendQuestion(question: string): Promise<void> {
    const trimmed = question.trim();
    const sessionId = this.state.activeSessionId;
    if (
      trimmed.length === 0 ||
      sessionId === null ||
      this.state.isLoading ||
      this.state.isSendingChat ||
      this.state.isGeneratingReport
    ) {
      return;
    }
    this.chatAbort?.abort();
    const controller = new AbortController();
    this.chatAbort = controller;
    this.setState({
      isSendingChat: true,
      chatStream: { question: trimmed, answer: "" },
      chatError: null,
    });
    try {
      for await (const chunk of this.chats.streamAnswer(trimmed, sessionId, controller.signal)) {
        if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
          return;
        }
        const current = this.state.chatStream;
        this.setState({
          chatStream: {
            question: current?.question ?? trimmed,
            answer: `${current?.answer ?? ""}${chunk}`,
          },
        });
      }
      if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
        return;
      }
      const messages = await this.storage.getMessages(sessionId);
      const pairIds = messages
        .filter((message) => message.role === "assistant")
        .map((message) => message.id);
      const relevanceEntries = await Promise.all(
        pairIds.map(async (pairId) => {
          const relevant = await this.relevance.getRelevance(sessionId, pairId);
          return [pairId, relevant] as const;
        }),
      );
      if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
        return;
      }
      this.setState({
        messages,
        relevance: Object.fromEntries(relevanceEntries),
        isSendingChat: false,
        chatStream: null,
      });
    } catch (error) {
      if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
        return;
      }
      this.setState({
        isSendingChat: false,
        chatStream: null,
        chatError: errorText(error, CHAT_ERROR),
      });
    } finally {
      if (this.chatAbort === controller) {
        this.chatAbort = null;
      }
    }
  }

  async generateReport(): Promise<void> {
    const sessionId = this.state.activeSessionId;
    if (
      sessionId === null ||
      this.state.isLoading ||
      this.state.isGeneratingReport ||
      this.state.isSendingChat
    ) {
      return;
    }
    this.reportAbort?.abort();
    const controller = new AbortController();
    this.reportAbort = controller;
    const previousReport = this.state.report;
    this.setState({
      isGeneratingReport: true,
      reportProgress: "planning",
      reportStream: "",
      reportError: null,
      downloadNotice: null,
    });
    try {
      for await (const event of this.reports.generateReport(sessionId, controller.signal)) {
        if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
          return;
        }
        if (event.type === "progress") {
          this.setState({ reportProgress: event.stage });
          continue;
        }
        if (event.type === "delta") {
          this.setState({ reportStream: `${this.state.reportStream}${event.text}` });
          continue;
        }
        if (event.type === "done") {
          this.setState({
            report: event.report,
            isGeneratingReport: false,
            reportProgress: null,
            reportStream: "",
            reportError: null,
            downloadNotice: null,
          });
          return;
        }
        const report = await this.loadReportAfterFailure(sessionId, previousReport);
        if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
          return;
        }
        this.setState({
          report,
          isGeneratingReport: false,
          reportProgress: null,
          reportStream: "",
          reportError: event.error,
          downloadNotice: null,
        });
        return;
      }
      if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
        return;
      }
      const report = await this.loadReportAfterFailure(sessionId, previousReport);
      if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
        return;
      }
      this.setState({
        report,
        isGeneratingReport: false,
        reportProgress: null,
        reportStream: "",
        reportError: REPORT_STREAM_ERROR,
        downloadNotice: null,
      });
    } catch (error) {
      if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
        return;
      }
      const report = await this.loadReportAfterFailure(sessionId, previousReport);
      if (controller.signal.aborted || this.state.activeSessionId !== sessionId) {
        return;
      }
      this.setState({
        report,
        isGeneratingReport: false,
        reportProgress: null,
        reportStream: "",
        reportError: errorText(error, REPORT_ERROR),
        downloadNotice: null,
      });
    } finally {
      if (this.reportAbort === controller) {
        this.reportAbort = null;
      }
    }
  }

  private async loadReportAfterFailure(
    sessionId: string,
    fallback: SessionReport | null,
  ): Promise<SessionReport | null> {
    try {
      return await this.reports.getReport(sessionId);
    } catch {
      return fallback;
    }
  }

  cancelReportGeneration(): void {
    const controller = this.reportAbort;
    this.reportAbort = null;
    controller?.abort();
    this.setState({
      isGeneratingReport: false,
      reportProgress: null,
      reportStream: "",
      reportError: null,
    });
  }

  async downloadReport(): Promise<void> {
    const session = this.state.sessions.find((item) => item.id === this.state.activeSessionId);
    if (session === undefined) {
      return;
    }
    if (this.state.report === null) {
      this.setState({ downloadNotice: NO_REPORT_MESSAGE });
      return;
    }
    if (this.state.isLoading || this.state.isGeneratingReport || this.state.isSendingChat) {
      return;
    }
    this.setState({ downloadNotice: null, reportError: null });
    try {
      await this.exporter.download(session.title, this.state.report);
    } catch {
      this.setState({ reportError: DOWNLOAD_ERROR });
    }
  }

  async eraseHistory(confirmed: boolean): Promise<void> {
    if (
      !confirmed ||
      this.state.isLoading ||
      this.state.isGeneratingReport ||
      this.state.isSendingChat
    ) {
      return;
    }
    const sessionId = this.state.activeSessionId;
    if (sessionId === null) {
      return;
    }
    this.setState({ isLoading: true, error: null });
    try {
      await this.eraser.eraseHistory(sessionId);
      this.setState({
        messages: [],
        report: null,
        relevance: {},
        chatStream: null,
        chatError: null,
        reportProgress: null,
        reportStream: "",
        reportError: null,
        downloadNotice: null,
        isLoading: false,
      });
    } catch {
      this.setState({ isLoading: false, error: ERASE_HISTORY_ERROR });
    }
  }

  async eraseReport(confirmed: boolean): Promise<void> {
    if (
      !confirmed ||
      this.state.isLoading ||
      this.state.isGeneratingReport ||
      this.state.isSendingChat ||
      this.state.report === null
    ) {
      return;
    }
    const sessionId = this.state.activeSessionId;
    if (sessionId === null) {
      return;
    }
    this.setState({ isLoading: true, error: null });
    try {
      await this.eraser.eraseReport(sessionId);
      this.setState({
        report: null,
        reportProgress: null,
        reportStream: "",
        reportError: null,
        downloadNotice: null,
        isLoading: false,
      });
    } catch {
      this.setState({ isLoading: false, error: ERASE_REPORT_ERROR });
    }
  }

  dismissDownloadNotice(): void {
    this.setState({ downloadNotice: null });
  }

  dismissError(): void {
    this.setState({ error: null });
  }
}
