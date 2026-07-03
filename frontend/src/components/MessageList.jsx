import { useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import StepList from "./StepList";
import { useAuth } from "../context/AuthContext";
import { BookOpen, Compass, HelpCircle, GitCompare } from "lucide-react";

export default function MessageList({ messages, isStreaming, steps, onSendPrompt }) {
  const bottomRef = useRef(null);
  const { user } = useAuth();
  const firstName = user?.name ? user.name.split(" ")[0] : "there";

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const quickPrompts = [
    {
      title: "Literature Review",
      description: "Synthesize literature and themes across uploaded papers",
      prompt: "Summarize the key contributions, methodology, and common themes across my uploaded papers.",
      icon: BookOpen,
    },
    {
      title: "Compare Papers",
      description: "Compare experimental results, baselines, and datasets",
      prompt: "Compare the experimental results, metrics, and datasets used across these documents.",
      icon: GitCompare,
    },
    {
      title: "Explain Mathematics",
      description: "Break down equations, formulas, and derivations",
      prompt: "Explain the mathematical formulation, equations, and core loss functions described in the paper.",
      icon: Compass,
    },
    {
      title: "Gap Analysis",
      description: "Extract limitations, gaps, and future research work",
      prompt: "Identify the limitations, research gaps, and suggested future work in this literature.",
      icon: HelpCircle,
    },
  ];

  if (!messages || messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 overflow-y-auto bg-[var(--background)]">
        <div className="max-w-2xl w-full text-center flex flex-col items-center gap-6 my-auto">
          {/* Brand header */}
          <h2
            className="text-4xl sm:text-5xl font-semibold text-[var(--foreground)] tracking-tight"
            style={{ fontFamily: '"Playfair Display", Georgia, serif' }}
          >
            How can I help you today, {firstName}?
          </h2>
          <p
            className="text-base text-[var(--muted-foreground)] leading-relaxed max-w-md"
            style={{ fontFamily: '"Inter", sans-serif' }}
          >
            Upload papers, audio recordings, or images to begin a multi-document synthesis and search.
          </p>

          {/* Quick Prompts Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full mt-6 text-left">
            {quickPrompts.map((item, idx) => {
              const Icon = item.icon;
              return (
                <button
                  key={idx}
                  onClick={() => onSendPrompt?.(item.prompt)}
                  className="bg-white border border-[var(--border-light)] hover:border-[var(--brand-terracotta)] p-4 rounded-xl shadow-sm hover:shadow-md cursor-pointer text-left transition-all duration-200 group flex flex-col gap-2"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[var(--brand-tan-bg)] text-[var(--brand-terracotta)] flex items-center justify-center group-hover:bg-[var(--brand-terracotta)] group-hover:text-white transition-all">
                      <Icon size={16} />
                    </div>
                    <span
                      className="font-semibold text-sm text-[var(--foreground)]"
                      style={{ fontFamily: '"Inter", sans-serif' }}
                    >
                      {item.title}
                    </span>
                  </div>
                  <p
                    className="text-xs text-[var(--muted-foreground)] leading-relaxed mt-1"
                    style={{ fontFamily: '"Inter", sans-serif' }}
                  >
                    {item.description}
                  </p>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // Check if the last assistant message already has content (tokens have arrived)
  const lastMessage = messages[messages.length - 1];
  const hasTokens =
    lastMessage?.role === "assistant" && lastMessage?.content?.length > 0;

  return (
    <div className="flex-1 overflow-y-auto px-6 sm:px-8 py-6 bg-[var(--background)]">
      <div className="max-w-3xl mx-auto flex flex-col gap-8">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Streaming & Step List indicator */}
        {isStreaming && (
          <div className="flex gap-4 items-start w-full">
            <div className="w-8 h-8 rounded-full bg-[var(--brand-terracotta)] text-white flex items-center justify-center font-bold text-xs select-none shrink-0 shadow-sm mt-1">
              Z
            </div>
            <div className="flex-1 max-w-[85%] bg-transparent p-0 pl-1">
              <StepList steps={steps} collapsed={hasTokens} />
              
              {!hasTokens && (
                <div className="flex gap-2 items-center h-6 mt-2 pl-1">
                  <div className="streaming-dot bg-[var(--brand-terracotta)]" />
                  <div className="streaming-dot bg-[var(--brand-terracotta)]" />
                  <div className="streaming-dot bg-[var(--brand-terracotta)]" />
                </div>
              )}
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
