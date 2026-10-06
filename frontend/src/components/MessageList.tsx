import { Message } from "../lib/api";

interface MessageListProps {
  messages: Message[];
  streaming: string;
}

export function MessageList({ messages, streaming }: MessageListProps) {
  if (messages.length === 0 && !streaming) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="max-w-md text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-100 text-3xl text-brand-600">
            💬
          </div>
          <h2 className="text-xl font-semibold text-slate-800">
            How can I help you today?
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Ask about our documentation, get account information, or file a
            support ticket.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === "user"
                ? "bg-brand-600 text-white"
                : "border border-slate-200 bg-white text-slate-800"
            }`}
          >
            {msg.content}
          </div>
        </div>
      ))}

      {streaming && (
        <div className="flex justify-start">
          <div className="max-w-[80%] whitespace-pre-wrap rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-relaxed text-slate-800">
            {streaming}
            <span className="ml-1 inline-block h-4 w-2 animate-pulse bg-brand-400 align-middle" />
          </div>
        </div>
      )}
    </div>
  );
}
