import { Conversation } from "../lib/api";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onLogout: () => void;
  onDelete: (id: string) => void;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onLogout,
  onDelete,
}: SidebarProps) {
  return (
    <aside className="flex h-full w-72 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <button
          onClick={onNewChat}
          className="btn-primary w-full"
        >
          + New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {conversations.length === 0 ? (
          <p className="px-3 py-6 text-center text-sm text-slate-400">
            No conversations yet
          </p>
        ) : (
          <ul className="space-y-1">
            {conversations.map((conv) => (
              <li key={conv.id} className="group flex items-center">
                <button
                  onClick={() => onSelect(conv.id)}
                  className={`flex-1 truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                    activeId === conv.id
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-700 hover:bg-slate-100"
                  }`}
                >
                  {conv.title || "Untitled"}
                </button>
                <button
                  onClick={() => onDelete(conv.id)}
                  title="Delete conversation"
                  className="mr-1 rounded p-1 text-slate-400 opacity-0 transition hover:bg-red-50 hover:text-red-600 group-hover:opacity-100"
                >
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M9 7V4a1 1 0 011-1h4a1 1 0 011 1v3"
                    />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="border-t border-slate-200 p-4">
        <button
          onClick={onLogout}
          className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-600 transition hover:bg-slate-100"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
