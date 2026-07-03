import { useState } from "react";
import { Trash2, Check, X, MessageSquare } from "lucide-react";

export default function ConversationList({
  conversations,
  activeConversationId,
  onSelect,
  onDelete,
}) {
  const [confirmingDeleteId, setConfirmingDeleteId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  function handleDeleteClick(e, convId) {
    e.stopPropagation();
    setConfirmingDeleteId(convId);
  }

  function handleCancelDelete(e) {
    e.stopPropagation();
    setConfirmingDeleteId(null);
  }

  async function handleConfirmDelete(e, convId) {
    e.stopPropagation();
    setConfirmingDeleteId(null);
    setDeletingId(convId);
    // Wait for fade-out animation to finish before removing
    setTimeout(() => {
      onDelete(convId);
      setDeletingId(null);
    }, 280);
  }

  if (!conversations || conversations.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center px-6">
        <p
          className="text-xs text-[var(--muted-foreground)] text-center font-medium"
          style={{ fontFamily: '"Inter", sans-serif' }}
        >
          No conversations yet
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-2 flex flex-col gap-0.5">
      {conversations.map((conv) => {
        const isActive = conv.id === activeConversationId;
        const isConfirming = confirmingDeleteId === conv.id;
        const isDeleting = deletingId === conv.id;

        const timestamp = new Date(conv.createdAt).toLocaleDateString([], {
          month: "short",
          day: "numeric",
        });

        const lastMessage =
          conv.messages && conv.messages.length > 0
            ? conv.messages[conv.messages.length - 1]
            : null;
        const snippet = lastMessage?.content
          ? lastMessage.content.substring(0, 30)
          : "";

        if (isConfirming) {
          return (
            <div
              key={conv.id}
              className={`conv-confirm-row mx-2 my-0.5 p-3 rounded-xl border border-[var(--border-light)] ${
                isActive
                  ? "bg-[var(--brand-hover-bg)]"
                  : "bg-white/40"
              }`}
            >
              <div
                className="text-[11px] text-[var(--foreground)] font-semibold truncate mb-2"
                style={{ fontFamily: '"Inter", sans-serif' }}
              >
                Delete chat?
              </div>
              <div className="flex gap-2">
                <button
                  onClick={(e) => handleConfirmDelete(e, conv.id)}
                  className="conv-delete-confirm-btn flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg bg-[var(--brand-terracotta)] text-white hover:opacity-90 transition-all cursor-pointer border-none"
                  style={{ fontFamily: '"Inter", sans-serif' }}
                >
                  <Check size={10} strokeWidth={3} />
                  Delete
                </button>
                <button
                  onClick={handleCancelDelete}
                  className="conv-delete-cancel-btn flex items-center gap-1 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-lg bg-white text-[var(--muted-foreground)] hover:text-[var(--foreground)] border border-[var(--border-light)] transition-all cursor-pointer"
                  style={{ fontFamily: '"Inter", sans-serif' }}
                >
                  <X size={10} strokeWidth={3} />
                  Cancel
                </button>
              </div>
            </div>
          );
        }

        return (
          <div
            key={conv.id}
            className={`conv-row group relative mx-2 my-0.5 rounded-xl text-left cursor-pointer transition-all duration-150 ${
              isDeleting ? "conv-deleting" : ""
            } ${
              isActive
                ? "bg-[var(--brand-hover-bg)] text-[var(--foreground)] shadow-sm"
                : "text-[var(--foreground)] hover:bg-[var(--brand-hover-bg)]/40"
            }`}
          >
            {/* Main clickable area */}
            <button
              onClick={() => onSelect(conv.id)}
              className="w-full text-left px-3 py-2.5 pr-8 block flex items-start gap-2.5 rounded-xl border-none cursor-pointer bg-transparent"
            >
              <MessageSquare size={14} className="text-[var(--muted-foreground)] shrink-0 mt-0.5 opacity-60" />
              <div className="flex-1 min-w-0">
                <div
                  className="text-xs font-semibold text-[var(--foreground)] truncate"
                  style={{ fontFamily: '"Inter", sans-serif' }}
                >
                  {conv.title}
                </div>
                <div
                  className="text-[10px] mt-0.5 text-[var(--muted-foreground)] truncate flex items-center gap-1 opacity-70"
                  style={{ fontFamily: '"Inter", sans-serif' }}
                >
                  <span>{timestamp}</span>
                  {snippet && (
                    <>
                      <span>·</span>
                      <span className="truncate">{snippet}</span>
                    </>
                  )}
                </div>
              </div>
            </button>

            {/* Hover-reveal delete button */}
            <button
              onClick={(e) => handleDeleteClick(e, conv.id)}
              className="delete-btn absolute right-2.5 top-1/2 -translate-y-1/2 p-1 text-[var(--muted-foreground)] hover:text-[var(--brand-terracotta)] hover:bg-white/80 rounded-md opacity-0 group-hover:opacity-100 border-none transition-all duration-150 cursor-pointer"
              title="Delete conversation"
              aria-label="Delete conversation"
            >
              <Trash2 size={12} strokeWidth={2} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
