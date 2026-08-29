export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0B0F17',
          card: '#131926',
          border: '#1E293B',
          hover: '#1E293B',
          text: '#F8FAFC',
          muted: '#94A3B8'
        },
        brand: {
          blue: '#3B82F6',
          cyan: '#06B6D4',
          emerald: '#10B981',
          amber: '#F59E0B',
          rose: '#EF4444',
          purple: '#8B5CF6'
        }
      }
    },
  },
  plugins: [],
}
