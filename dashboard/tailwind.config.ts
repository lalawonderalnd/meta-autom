import type { Config } from 'tailwindcss'

export default {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#07080a',
        surface: '#0e1014',
        'surface-elevated': '#14171c',
        border: '#1f2329',
        'border-strong': '#2a2f37',
        foreground: '#e6e8eb',
        'foreground-muted': '#8a8f98',
        'foreground-subtle': '#5a606b',
        'accent-cyan': '#4dd4ff',
        'accent-amber': '#ffb547',
        'accent-blue': '#5b8dff',
        'accent-magenta': '#ff5fb8',
        'accent-red': '#ff5247',
        'accent-violet': '#a06bff',
        'accent-green': '#5ce086',
      },
      fontFamily: {
        display: ['Departure Mono', 'monospace'],
        body: ['Manrope', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 8px rgba(77, 212, 255, 0.4)',
        'glow-amber': '0 0 8px rgba(255, 181, 71, 0.4)',
      },
    },
  },
  plugins: [],
} satisfies Config
