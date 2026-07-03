import axios from "axios";

/**
 * Base URL for all API requests.
 * In development: reads VITE_API_URL from .env (defaults to localhost:8000).
 * In production builds: set VITE_API_URL to your deployed backend URL at build time.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || "https://multimodal-rag-pipeline-by-langgraph-production.up.railway.app";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
