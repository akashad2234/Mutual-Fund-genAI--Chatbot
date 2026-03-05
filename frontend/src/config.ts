// Base URL for the backend API.
// In production (Netlify), set VITE_API_BASE_URL to your Render backend root URL.
// For local development, we default to the local backend on port 8001.
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001";

