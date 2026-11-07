import { useState } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { agUIAdapter } from "@openuidev/react-headless";
import {
  AgentInterface,
  type AgentInterfaceComponents,
  type AssistantMessage,
  type UserMessage,
} from "@openuidev/react-ui";

const llm = {
  send: async () => new Response("data: [DONE]\n\n"),
  streamProtocol: agUIAdapter(),
};
const storage = {
  thread: {
    listThreads: async () => ({ threads: [] }),
    createThread: async () => ({ id: "t1", title: "Spike", createdAt: Date.now() }),
    getMessages: async () => [],
    updateThread: async (thread: unknown) => thread,
    deleteThread: async () => undefined,
  },
};

const deleted: string[] = [];

function PairControls({ id, role }: { id: string; role: string }) {
  const [relevant, setRelevant] = useState(true);
  return (
    <div data-pair-id={id} data-role={role} data-relevant={relevant}>
      <button type="button" data-action="relevance" onClick={() => setRelevant(!relevant)}>
        relevant
      </button>
      <button type="button" data-action="delete" onClick={() => deleted.push(id)}>
        delete
      </button>
    </div>
  );
}

const PairAssistantMessage = ({ message }: { message: AssistantMessage }) => (
  <PairControls id={message.id} role="assistant" />
);

const PairUserMessage = ({ message }: { message: UserMessage }) => (
  <PairControls id={message.id} role="user" />
);

const components: AgentInterfaceComponents = {
  AssistantMessage: PairAssistantMessage,
  UserMessage: PairUserMessage,
};

describe("TASK-019 per-pair controls", () => {
  it("accepts the message overrides in the react-ui chat layout", () => {
    const html = renderToStaticMarkup(
      <AgentInterface
        agentName="Spike"
        components={components}
        llm={llm}
        storage={storage as never}
      />,
    );
    expect(html).toContain("Spike");
  });

  it("renders a relevance toggle and delete action for each message", () => {
    const html = renderToStaticMarkup(
      <>
        <PairAssistantMessage
          message={{ id: "a1", role: "assistant", content: "Synthetic answer" }}
        />
        <PairUserMessage message={{ id: "u1", role: "user", content: "Synthetic question" }} />
      </>,
    );
    expect(html.match(/data-action="relevance"/g)).toHaveLength(2);
    expect(html.match(/data-action="delete"/g)).toHaveLength(2);
    expect(html).toContain('data-role="assistant"');
    expect(html).toContain('data-role="user"');
  });
});
