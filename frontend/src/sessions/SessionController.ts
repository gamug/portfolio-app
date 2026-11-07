import type { ChatStorage, Message, Thread, UserMessage } from "@openuidev/react-ui";

export type ThreadStorage = ChatStorage["thread"];

export type SessionReport = {
  openui_lang: string;
  incomplete: boolean;
  created_at: string;
  updated_at: string;
};

export interface ReportClient {
  getReport(sessionId: string): Promise<SessionReport | null>;
}

export interface RelevanceClient {
  getRelevance(sessionId: string, pairId: string): Promise<boolean>;
  setRelevance(sessionId: string, pairId: string, relevant: boolean): Promise<boolean>;
}

export type SessionState = {
  sessions: Thread[];
  activeSessionId: string | null;
  messages: Message[];
  report: SessionReport | null;
  relevance: Record<string, boolean>;
  isLoading: boolean;
  error: string | null;
};

const LOAD_ERROR = "Could not load sessions. Please try again.";
const CREATE_ERROR = "Could not create a session. Please try again.";
const RENAME_ERROR = "Could not rename the session. Please try again.";
const DELETE_ERROR = "Could not delete the session. Please try again.";
const SELECT_ERROR = "Could not load the session. Please try again.";
const RELEVANCE_ERROR = "Could not update the relevance. Please try again.";

function newUserMessage(): UserMessage {
  const id =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `session-${Date.now()}`;
  return { id, role: "user", content: "New Chat" };
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
  };
  private readonly listeners = new Set<() => void>();

  constructor(
    private readonly storage: ThreadStorage,
    private readonly reports: ReportClient,
    private readonly relevance: RelevanceClient,
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

  async initialize(): Promise<void> {
    this.setState({ isLoading: true, error: null });
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
    this.setState({ isLoading: true, error: null });
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
    this.setState({ isLoading: true, error: null });
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
    this.setState({ isLoading: true, error: null });
    const deletingActive = this.state.activeSessionId === sessionId;
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

  async toggleRelevance(pairId: string): Promise<void> {
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

  dismissError(): void {
    this.setState({ error: null });
  }
}
