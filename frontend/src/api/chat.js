import client from "./client";

/**
 * Upload files to the backend.
 * @param {File[]} files - Array of File objects
 * @returns {Promise<{ file_paths: string[], file_names: string[], count: number }>}
 */

export async function uploadFiles(files) {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });

  const response = await client.post("/api/v1/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

/**
 * Send a chat message to the backend (non-streaming).
 * @param {{ query: string, file_paths: string[], thread_id: string | null }} params
 * @returns {Promise<{ thread_id: string, final_answer: string, task: string }>}
 */
export async function sendMessage({ query, file_paths = [], thread_id = null }) {
  const response = await client.post("/api/v1/chat", {
    query,
    file_paths,
    thread_id,
  });

  return response.data;
}

/**
 * Stream a chat message from the backend via SSE.
 * Uses fetch() (not axios) for proper ReadableStream support.
 *
 * @param {{ query: string, file_paths: string[], thread_id: string | null }} params
 * @param {{ onToken: Function, onStatus: Function, onDone: Function, onError: Function, onClarification: Function }} callbacks
 * @returns {Promise<void>}
 */
export async function streamMessage(
  { query, file_paths = [], thread_id = null },
  { onToken, onStatus, onDone, onError, onClarification },
  endpoint = `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/v1/chat/stream`
) {
  const token = localStorage.getItem("auth_token");
  const response = await fetch(endpoint, {
    method: "POST",
    headers:
    {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    }
    ,
    body: JSON.stringify({ query, file_paths, thread_id }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE lines from buffer
    const lines = buffer.split("\n");
    // Keep the last (possibly incomplete) line in the buffer
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data: ")) continue;

      try {
        const payload = JSON.parse(trimmed.slice(6));

        switch (payload.type) {
          case "token":
            onToken?.(payload);
            break;
          case "status":
            onStatus?.(payload);
            break;
          case "done":
            onDone?.(payload);
            break;
          case "error":
            onError?.(payload);
            break;
          case "clarification":
            onClarification?.(payload);
            break;
          default:
            break;
        }
      } catch {
        // Skip malformed JSON lines
      }
    }
  }
}


/**
 * Resume an interrupted graph with clarification answer.
 */
export async function streamClarification(
  { query, thread_id },
  callbacks
) {
  return streamMessage(
    { query, file_paths: [], thread_id },
    callbacks,
    `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/v1/chat/clarify`
  );
}