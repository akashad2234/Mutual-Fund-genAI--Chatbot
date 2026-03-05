// Base URL for the backend API.
// In production (Netlify), this should normally point to your Render backend URL.
// You can override it via the VITE_API_BASE_URL env var on Netlify.
const PROD_DEFAULT_API_BASE_URL = "https://YOUR-RENDER-BACKEND-URL";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.PROD ? PROD_DEFAULT_API_BASE_URL : "http://localhost:8001");

