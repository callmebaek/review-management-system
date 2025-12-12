/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'IBM Plex Sans KR', 'system-ui', '-apple-system', 'sans-serif'],
        inter: ['Inter', 'sans-serif'],
        'ibm-kr': ['IBM Plex Sans KR', 'sans-serif'],
      },
      fontWeight: {
        'heading': '800',
        'title': '900',
      },
    },
  },
  plugins: [],
}








