import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import { useAuth } from "./AuthContext";

const ChatContext = createContext(null);

/**
 * Returns a user-scoped localStorage key so every user
 * gets their own independent conversation history.
 */
function storageKeyForUser(userId) {
  return userId ? `zeus_conversations_${userId}` : null;
}

function loadConversations(userId) {
  const key = storageKeyForUser(userId);
  if (!key) return [];
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

function saveConversations(userId, conversations) {
  const key = storageKeyForUser(userId);
  if (!key) return;
  localStorage.setItem(key, JSON.stringify(conversations));
}

export function ChatProvider({ children }) {
  const { user } = useAuth();
  const userId = user?.id || null;

  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [pendingClarification, setPendingClarification] = useState(null);
  // Shape: { threadId: string, question: string, conversationId: string } | null

  // Load conversations whenever the logged-in user changes
  useEffect(() => {
    if (userId) {
      setConversations(loadConversations(userId));
    } else {
      setConversations([]);
    }
    setActiveConversationId(null);
    setPendingClarification(null);
  }, [userId]);

  // Persist conversations whenever they change (scoped to current user)
  useEffect(() => {
    if (userId) {
      saveConversations(userId, conversations);
    }
  }, [conversations, userId]);

  const activeConversation = conversations.find(
    (c) => c.id === activeConversationId
  ) || null;

  const createConversation = useCallback(() => {
    const newConversation = {
      id: uuidv4(),
      title: "New Conversation",
      createdAt: new Date().toISOString(),
      messages: [],
      threadId: null,
    };
    setConversations((prev) => [newConversation, ...prev]);
    setActiveConversationId(newConversation.id);
    return newConversation.id;
  }, []);

  const addMessage = useCallback((conversationId, message) => {
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id !== conversationId) return conv;

        const newMessages = [...conv.messages, message];

        // Update title from first user message
        let title = conv.title;
        if (
          message.role === "user" &&
          conv.messages.filter((m) => m.role === "user").length === 0
        ) {
          title =
            message.content.length > 40
              ? message.content.substring(0, 40) + "..."
              : message.content;
        }

        return { ...conv, messages: newMessages, title };
      })
    );
  }, []);

  const updateLastAssistantMessage = useCallback((conversationId, content) => {
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id !== conversationId) return conv;

        const messages = [...conv.messages];
        const lastIdx = messages.length - 1;
        if (lastIdx >= 0 && messages[lastIdx].role === "assistant") {
          messages[lastIdx] = { ...messages[lastIdx], content };
        }

        return { ...conv, messages };
      })
    );
  }, []);

  const setThreadId = useCallback((conversationId, threadId) => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === conversationId ? { ...conv, threadId } : conv
      )
    );
  }, []);

  const deleteConversation = useCallback(
    (conversationId) => {
      setConversations((prev) => prev.filter((c) => c.id !== conversationId));
      if (activeConversationId === conversationId) {
        setActiveConversationId(null);
      }
    },
    [activeConversationId]
  );

  return (
    <ChatContext.Provider
      value={{
        conversations,
        activeConversationId,
        activeConversation,
        isStreaming,
        setActiveConversationId,
        createConversation,
        addMessage,
        updateLastAssistantMessage,
        setThreadId,
        setIsStreaming,
        deleteConversation,
        pendingClarification,
        setPendingClarification,

      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
