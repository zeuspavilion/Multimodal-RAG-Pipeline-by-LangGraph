import ConversationList from "./ConversationList";
import UserAccountBlock from "./UserAccountBlock";
import { useChat } from "../context/ChatContext";
import { Plus } from "lucide-react";

export default function Sidebar() {
  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    createConversation,
    deleteConversation,
  } = useChat();

  return (
    <div className="w-[var(--sidebar-width)] shrink-0 border-r border-[var(--border-light)] h-screen flex flex-col bg-[var(--brand-tan-bg)]">
      {/* App name */}
      <div className="p-6 pb-4">
        <h1
          className="text-xl font-bold tracking-tight text-[var(--foreground)]"
          style={{ fontFamily: '"Playfair Display", Georgia, serif' }}
        >
          Zeus
        </h1>
      </div>

      {/* New Chat button */}
      <div className="px-4 pb-3">
        <button
          id="new-chat-button"
          onClick={createConversation}
          className="w-full bg-white hover:bg-gray-50 text-[var(--foreground)] border border-[var(--border-light)] py-2.5 rounded-xl font-semibold cursor-pointer transition-all duration-150 flex items-center justify-center gap-1.5 shadow-sm"
          style={{
            fontFamily: '"Inter", sans-serif',
            fontSize: "13px",
          }}
        >
          <Plus size={15} className="text-[var(--brand-terracotta)]" strokeWidth={2.5} />
          New Chat
        </button>
      </div>

      {/* Divider */}
      <div className="h-px bg-[var(--border-light)] mx-4 mb-2" />

      {/* Conversation list */}
      <ConversationList
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelect={setActiveConversationId}
        onDelete={deleteConversation}
      />

      {/* User account block */}
      <UserAccountBlock />
    </div>
  );
}
