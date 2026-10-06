import { useCallback, useEffect, useRef, useState } from "react";

import { ChatInput } from "./components/ChatInput";
import { MessageList } from "./components/MessageList";
import { Sidebar } from "./components/Sidebar";
import { useAuth, authHeaders } from "./lib/auth";
import {
  Conversation,
  deleteConversation,
  getConversationDetail,
  listConversations,
} from "./lib/api";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export function App() {
  const { token, logout } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const loadConversations = useCallback(async () => {
    if (!token) return;
    try {
      const convs = await listConversations(token);
      setConversations(convs);
    } catch {
      // ignore - maybe not authenticated
    }
  }, [token]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, streaming]);

  const loadConversation = async (id: string) => {
    if (!token) return;
    setActiveId(id);
    try {
      const detail = await getConversationDetail(token, id);
      setMessages(
        detail.messages.map((m) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          created_at: m.created_at,
        }))
      );
      setStreaming("");
    } catch {
      // ignore
    }
  };

  const newChat = () => {
    setActiveId(null);
    setMessages([]);
    setStreaming("");
  };

  const handleSend = async (message: string) => {
    if (!token) return;
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: message, created_at: new Date().toISOString() },
    ]);
    setLoading(true);
    setStreaming("");

    let conversationId = activeId ?? undefined;
    let fullText = "";

    try {
      const res = await fetch("/chat/stream", {
        method: "POST",
        headers: {
          ...authHeaders(token),
          Accept: "text/event-stream",
        },
        body: JSON.stringify({ message, conversation_id: conversationId }),
      });

      if (!res.ok || !res.body) {
        throw new Error("Failed to start stream");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6);
          if (payload === "[DONE]") continue;
          try {
            const data = JSON.parse(payload);
            if (data.token) {
              fullText += data.token;
              setStreaming(fullText);
            }
            if (data.conversation_id) {
              conversationId = data.conversation_id;
              setActiveId(data.conversation_id);
            }
          } catch {
            // skip malformed payloads
          }
        }
      }

      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: fullText, created_at: new Date().toISOString() },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            err instanceof Error
              ? `Error: ${err.message}`
              : "Something went wrong. Please try again.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setStreaming("");
      setLoading(false);
      loadConversations();
    }
  };

  const handleDelete = async (id: string) => {
    if (!token) return;
    await deleteConversation(token, id);
    if (id === activeId) newChat();
    await loadConversations();
  };

  return (
    <div className="flex h-screen">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={loadConversation}
        onNewChat={newChat}
        onLogout={logout}
        onDelete={handleDelete}
      />

      <main className="flex flex-1 flex-col">
        <header className="border-b border-slate-200 bg-white px-6 py-4">
          <h1 className="text-lg font-semibold text-slate-900">
            SmartAI Support Assistant
          </h1>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
          <MessageList messages={messages} streaming={streaming} />
        </div>

        <ChatInput onSend={handleSend} disabled={loading} />
      </main>
    </div>
  );
}
