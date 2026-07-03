import { useState } from "react";
import { ArrowUp, HelpCircle } from "lucide-react";

export default function ClarificationBar({ question, onSubmit, disabled }) {
  const [text, setText] = useState("");

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (text.trim() && !disabled) handleSubmit();
    }
  }

  function handleSubmit() {
    if (!text.trim() || disabled) return;
    onSubmit(text.trim());
    setText("");
  }

  return (
    <div className="p-4 bg-[var(--background)]">
      <div className="max-w-3xl mx-auto bg-white rounded-2xl border border-[var(--brand-terracotta)]/40 shadow-sm focus-within:shadow-md transition-all p-4.5 flex flex-col gap-2">
        <div className="flex items-center gap-2 text-[var(--brand-terracotta)] font-semibold text-xs mb-1.5" style={{ fontFamily: '"Inter", sans-serif' }}>
          <HelpCircle size={14} className="animate-pulse" />
          <span>Zeus Clarification Request</span>
        </div>

        {/* Question bubble */}
        <p className="text-sm font-medium text-[var(--foreground)] mb-2 pl-0.5 leading-relaxed" style={{ fontFamily: '"Inter", sans-serif' }}>
          {question}
        </p>

        {/* Input panel */}
        <div className="bg-[var(--brand-tan-bg)]/50 rounded-xl border border-[var(--border-light)] p-2.5 flex flex-col gap-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your response..."
            disabled={disabled}
            rows={2}
            className="w-full bg-transparent text-[var(--foreground)] resize-none border-none outline-none placeholder:text-[var(--muted-foreground)] focus:ring-0 focus:outline-none"
            style={{
              fontFamily: '"Inter", sans-serif',
              fontSize: "13.5px",
              lineHeight: "1.5"
            }}
            autoFocus
          />
          <div className="flex justify-end border-t border-[var(--border-light)]/40 pt-2">
            <button
              onClick={handleSubmit}
              disabled={!text.trim() || disabled}
              className={`w-7.5 h-7.5 rounded-full flex items-center justify-center border-none cursor-pointer transition-all ${
                text.trim() && !disabled
                  ? "bg-[var(--brand-terracotta)] text-white hover:opacity-90 shadow-sm"
                  : "bg-gray-100 text-gray-300 cursor-not-allowed"
              }`}
            >
              <ArrowUp size={14} strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}