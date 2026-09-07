/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        graphite: {
          950: '#08090b',
          900: '#0c0d10',
          850: '#121317',
          800: '#17181d',
          700: '#202127',
          600: '#2c2d35',
          500: '#4a4c56',
        },
        ink: {
          primary: '#EDEEF1',
          secondary: '#9AA0AC',
          tertiary: '#6B7280',
          disabled: '#454952',
        },
        signal: {
          DEFAULT: '#2E56E8',
          strong: '#1C3FC4',
          soft: 'rgba(46,86,232,0.12)',
        },
        gold: {
          DEFAULT: '#E5A93B',
          strong: '#C88A1F',
          soft: 'rgba(229,169,59,0.12)',
        },
        buy: { DEFAULT: '#2FB866', soft: 'rgba(47,184,102,0.12)' },
        avoid: { DEFAULT: '#E5484D', soft: 'rgba(229,72,77,0.12)' },
        rarity: {
          contraband: '#e4ae39',
          covert: '#eb4b4b',
          classified: '#d32ce6',
          restricted: '#8847ff',
          milspec: '#4b69ff',
          industrial: '#5e98d9',
          consumer: '#b0c3d9',
        },
      },
      fontFamily: {
        sans: [
          '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', '"PingFang SC"',
          '"Microsoft YaHei"', '"Helvetica Neue"', 'Roboto', 'Arial', 'sans-serif',
        ],
        mono: [
          'ui-monospace', '"SF Mono"', '"Cascadia Code"', '"Roboto Mono"',
          'Menlo', 'Consolas', 'monospace',
        ],
      },
      borderRadius: {
        sm: '6px',
        md: '10px',
        lg: '14px',
      },
      boxShadow: {
        sm: '0 1px 2px rgba(0,0,0,0.4)',
        md: '0 8px 24px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.04)',
        lg: '0 20px 48px rgba(0,0,0,0.55)',
        'accent-glow': '0 0 0 1px rgba(46,86,232,0.35), 0 8px 24px rgba(46,86,232,0.22)',
      },
      transitionTimingFunction: {
        standard: 'cubic-bezier(.16,1,.3,1)',
      },
    },
  },
  plugins: [],
}
