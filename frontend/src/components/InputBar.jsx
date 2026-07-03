import { useState, useRef } from "react";
import { Paperclip, ArrowUp } from "lucide-react";
import FileChip from "./FileChip";

export default function InputBar({ onSend, disabled }) {
  const [text, setText] = useState("");
  const [files, setFiles] = useState([]);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const canSend = (text.trim().length > 0 || files.length > 0) && !disabled;

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSend) handleSend();
    }
  }

  function handleSend() {
    if (!canSend) return;
    onSend(text.trim(), files);
    setText("");
    setFiles([]);
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }

  function handleFileChange(e) {
    const newFiles = Array.from(e.target.files);
    setFiles((prev) => [...prev, ...newFiles]);
    // Reset input so the same file can be re-added if removed
    e.target.value = "";
  }

  function removeFile(fileToRemove) {
    setFiles((prev) => prev.filter((f) => f !== fileToRemove));
  }

  function handleTextareaInput(e) {
    const textarea = e.target;
    textarea.style.height = "auto";
    const maxHeight = 6 * 24; // approx 6 lines
    textarea.style.height = Math.min(textarea.scrollHeight, maxHeight) + "px";
  }

  return (
    <div className="p-4 bg-[var(--background)]">
      <div className="max-w-3xl mx-auto bg-white rounded-2xl border border-[var(--border-light)] shadow-sm focus-within:shadow-md focus-within:border-[var(--brand-terracotta)] transition-all p-3 flex flex-col gap-2">
        
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleTextareaInput}
          placeholder="Ask Zeus about a paper, compare methods, or explore a topic..."
          disabled={disabled}
          rows={1}
          className="w-full bg-white text-[var(--foreground)] resize-none border-none outline-none placeholder:text-[var(--muted-foreground)] focus:ring-0 focus:outline-none py-1.5 px-1"
          style={{
            fontFamily: '"Inter", sans-serif',
            fontSize: "14px",
            lineHeight: "1.5",
            maxHeight: `${6 * 24}px`,
          }}
        />

        {/* File preview row - sits inside the input card below text */}
        {files.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-2 pt-1 border-t border-[var(--border-light)]">
            {files.map((file, idx) => (
              <FileChip key={`${file.name}-${idx}`} file={file} onRemove={removeFile} />
            ))}
          </div>
        )}

        {/* Bottom row: attach + send */}
        <div className="flex justify-between items-center border-t border-gray-50 pt-2 px-1">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="bg-transparent border-none cursor-pointer p-1.5 rounded-full hover:bg-[var(--brand-tan-bg)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-all"
            aria-label="Attach files"
          >
            <Paperclip size={18} strokeWidth={2} />
          </button>

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="*/*"
            onChange={handleFileChange}
            className="hidden"
          />

          <button
            id="send-button"
            onClick={handleSend}
            disabled={!canSend}
            className={`w-8 h-8 rounded-full flex items-center justify-center border-none cursor-pointer transition-all ${
              canSend
                ? "bg-[var(--brand-terracotta)] text-white hover:opacity-90 shadow-sm"
                : "bg-gray-100 text-gray-300 cursor-not-allowed"
            }`}
            aria-label="Send message"
          >
            <ArrowUp size={16} strokeWidth={2.5} />
          </button>
        </div>
      </div>
    </div>
  );
}
