import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Copy, Check, FileText, Image as ImageIcon, FileAudio, File } from "lucide-react";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";
  const isError = message.role === "error";
  const [copied, setCopied] = useState(false);

  const timestamp = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  function handleCopy() {
    navigator.clipboard.writeText(message.content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  if (isError) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[85%] border-l-4 border-red-500 bg-red-50/50 p-4 rounded-r-xl">
          <p
            className="text-sm italic text-red-700"
            style={{ fontFamily: '"Inter", sans-serif' }}
          >
            Error: {message.content}
          </p>
        </div>
      </div>
    );
  }

  if (isUser) {
    return (
      <div className="group flex flex-col items-end w-full">
        <div className="max-w-[70%] bg-[#eae3d2] text-[var(--foreground)] px-4.5 py-3.5 rounded-2xl rounded-tr-sm shadow-sm">
          {message.files && message.files.length > 0 && (
            <div className="mb-2.5 flex flex-wrap gap-1.5">
              {message.files.map((fileName, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1 bg-white/70 border border-white/20 text-[var(--muted-foreground)] rounded-lg font-medium"
                  style={{ fontFamily: '"Inter", sans-serif' }}
                >
                  <FileText size={10} className="text-[var(--brand-terracotta)]" />
                  {fileName}
                </span>
              ))}
            </div>
          )}
          <p
            className="text-[15px] leading-relaxed whitespace-pre-wrap font-sans text-[var(--foreground)]"
            style={{ fontFamily: '"Inter", sans-serif' }}
          >
            {message.content}
          </p>
        </div>
        {timestamp && (
          <span
            className="text-[10px] text-[var(--muted-foreground)] mt-1.5 mr-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
            style={{ fontFamily: '"JetBrains Mono", monospace' }}
          >
            {timestamp}
          </span>
        )}
      </div>
    );
  }

  // Assistant message
  return (
    <div className="group flex gap-4 items-start w-full">
      {/* Zeus avatar icon */}
      <div className="w-8 h-8 rounded-full bg-[var(--brand-terracotta)] text-white flex items-center justify-center font-bold text-xs select-none shrink-0 shadow-sm mt-1">
        Z
      </div>

      <div className="relative flex-1 bg-transparent p-0 pl-1">
        <div
          className="markdown-content text-[16px] leading-relaxed text-[var(--foreground)]"
          style={{ fontFamily: '"Source Serif 4", Georgia, serif' }}
        >
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Copy button — appears on hover */}
        {message.content && (
          <button
            onClick={handleCopy}
            className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 bg-white hover:bg-gray-50 border border-[var(--border-light)] shadow-sm rounded-lg cursor-pointer p-1.5 text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
            aria-label="Copy message"
          >
            {copied ? (
              <Check size={13} strokeWidth={2.5} className="text-green-600" />
            ) : (
              <Copy size={13} strokeWidth={2} />
            )}
          </button>
        )}

        {timestamp && (
          <div className="mt-2.5">
            <span
              className="text-[10px] text-[var(--muted-foreground)] opacity-0 group-hover:opacity-100 transition-opacity duration-150"
              style={{ fontFamily: '"JetBrains Mono", monospace' }}
            >
              {timestamp}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
