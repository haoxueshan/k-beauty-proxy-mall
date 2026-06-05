import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1d1c1a",
        parchment: "#f7efe2",
        coral: "#f06449",
        moss: "#486b45",
        sand: "#d6b98f"
      },
      boxShadow: {
        card: "0 18px 50px rgba(29, 28, 26, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;
