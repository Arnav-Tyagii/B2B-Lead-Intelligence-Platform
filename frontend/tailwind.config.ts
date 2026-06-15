import type { Config } from "tailwindcss";

/**
 * Newsprint design tokens (see DESIGN_SYSTEM.md).
 * Single permanent light palette, zero border radius everywhere, hard offset
 * shadow, and the four font families wired as `font-serif | font-body |
 * font-sans | font-mono` utilities.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    // Zero radius EVERYWHERE — even if someone writes `rounded-lg`, it stays sharp.
    borderRadius: {
      none: "0",
      sm: "0",
      DEFAULT: "0",
      md: "0",
      lg: "0",
      xl: "0",
      "2xl": "0",
      "3xl": "0",
      full: "0",
    },
    extend: {
      colors: {
        ink: "#111111", // foreground / borders
        paper: "#F9F9F7", // background (newsprint off-white)
        divider: "#E5E5E0", // secondary borders
        accent: "#CC0000", // editorial red — used sparingly
      },
      fontFamily: {
        serif: ["'Playfair Display'", "'Times New Roman'", "serif"],
        body: ["Lora", "Georgia", "serif"],
        sans: ["Inter", "'Helvetica Neue'", "sans-serif"],
        mono: ["'JetBrains Mono'", "'Courier New'", "monospace"],
      },
      boxShadow: {
        // Hard offset "newspaper cutout" shadow for hover lift.
        hard: "4px 4px 0px 0px #111111",
      },
      maxWidth: {
        "screen-xl": "1280px",
      },
    },
  },
  plugins: [],
};

export default config;
