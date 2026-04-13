/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        slate: {
          750: '#293548',
          850: '#172033',
          950: '#0a1628',
        },
      },
    },
  },
  plugins: [],
}
