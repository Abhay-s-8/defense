import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV
    ? "http://127.0.0.1:5000"
    : "https://mastercard-ai-defense-backends.onrender.com");

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json"
  },
  timeout: 90000
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("mastercard_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("mastercard_token");
      localStorage.removeItem("mastercard_user");
    }

    return Promise.reject(error);
  }
);
