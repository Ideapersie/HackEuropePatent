import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          bg: "#0a0e1a",
          surface: "#111827",
          border: "#1f2937",
          accent: "#ef4444",
          amber: "#f59e0b",
          green: "#10b981",
          muted: "#6b7280",
          text: "#f9fafb",
          sub: "#9ca3af",
        },
      },
    },
  },
  plugins: [],
} satisfies Config;
