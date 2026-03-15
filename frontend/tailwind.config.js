/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './hooks/**/*.{js,ts,jsx,tsx}',
    './lib/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          base:    '#0a0a0a',
          surface: '#0d0d0d',
          card:    '#141414',
          border:  '#242424',
          sub:     '#1a1a1a',
          hover:   '#1c1c1c',
        },
        accent: {
          green:          '#3ECF8E',
          'green-dim':    'rgba(62,207,142,0.08)',
          'green-border': 'rgba(62,207,142,0.20)',
          'green-glow':   'rgba(62,207,142,0.25)',
          orange:         '#F5A623',
          red:            '#FF4757',
          blue:           '#3B82F6',
          purple:         '#8844ff',
        },
        text: {
          primary:   '#f0f0f0',
          secondary: '#8888aa',
          muted:     '#505050',
          dim:       '#333333',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan': 'scan 2s linear infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
      },
    },
  },
  plugins: [],
}
