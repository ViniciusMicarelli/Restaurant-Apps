/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Tokens da direção visual aprovada (2026-08-10, ver docs/logs/2026-08-10.md
      // Sessão 8). admin-web é ferramenta interna — sem White-Label por tenant
      // (isso existe só no customer-web, ver `apps/customer-web/src/theme/branding.ts`)
      // — então a paleta aqui é fixa, não variável de tenant.
      colors: {
        ink: {
          DEFAULT: '#1b1e27',
          soft: '#565c6b',
        },
        paper: '#f1f2f5',
        surface: {
          DEFAULT: '#ffffff',
          2: '#f8f8fa',
        },
        border: '#dde0e6',
        accent: {
          DEFAULT: '#c1541f',
          ink: '#ffffff',
          soft: '#f7e4d6',
        },
        good: {
          DEFAULT: '#3f7d5c',
          soft: '#e1efe7',
        },
        warning: {
          DEFAULT: '#a9781f',
          soft: '#f5ead1',
        },
        critical: {
          DEFAULT: '#b23a3a',
          soft: '#f6e1e1',
        },
        // Estado administrativo/transitório, não é problema nem "em uso"
        // (ex: mesa reservada) — completa os 4 tons distintos que o mapa
        // de mesas precisa (livre/reservada/ocupada/limpeza) sem pedir
        // emprestado o `critical`, que fica só pra estado que realmente
        // pede atenção urgente.
        info: {
          DEFAULT: '#3b5b8c',
          soft: '#e2e8f5',
        },
      },
      fontFamily: {
        // Cabeçalhos/rótulos das telas operacionais — lidas sob pressão,
        // não navegadas por prazer (mapa de mesas, KDS, dashboard).
        display: ['Futura', '"Futura PT"', '"Century Gothic"', '"URW Gothic"', '"Trebuchet MS"', 'sans-serif'],
        // Texto de interface (labels, corpo).
        body: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        // Números — dinheiro, contadores, timers. `font-variant-numeric:
        // tabular-nums` nos componentes que alinham dígitos em coluna.
        data: ['"SF Mono"', '"Cascadia Code"', 'Consolas', '"Liberation Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
