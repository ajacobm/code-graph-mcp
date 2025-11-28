/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom color palette for code graph visualization
        slate: {
          850: '#1a1f2e',
        },
      },
    },
  },
  plugins: [],
}
