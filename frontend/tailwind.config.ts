import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        panel: "#ffffff",
        line: "#dbe3ee",
      },
      boxShadow: {
        soft: "0 10px 30px rgba(23, 32, 51, 0.08)",
      },
    },
  },
  plugins: [],
} satisfies Config;
