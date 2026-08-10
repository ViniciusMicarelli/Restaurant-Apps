/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      // Tokens da direção visual aprovada (2026-08-10, ver docs/logs/2026-08-10.md
      // Sessão 8). `accent`/`paper`/`surface` REFERENCIAM as variáveis CSS do
      // White-Label existente (`src/theme/branding.ts`) em vez de duplicá-las —
      // continuam customizáveis por tenant. Só o texto/borda/estado é fixo.
      colors: {
        ink: {
          DEFAULT: 'var(--ink)',
          soft: 'var(--ink-soft)',
        },
        paper: 'var(--brand-bg)',
        surface: 'var(--brand-surface)',
        border: 'var(--border)',
        accent: 'var(--brand-primary)',
        good: {
          DEFAULT: 'var(--good)',
          soft: 'var(--good-soft)',
        },
        warning: {
          DEFAULT: 'var(--warning)',
          soft: 'var(--warning-soft)',
        },
        critical: {
          DEFAULT: 'var(--critical)',
          soft: 'var(--critical-soft)',
        },
      },
      fontFamily: {
        // Registro próprio do cardápio — a única tela lida por prazer, não
        // sob pressão (nome do prato em serifa itálica).
        menu: ['Georgia', '"Iowan Old Style"', '"Palatino Linotype"', '"Book Antiqua"', 'serif'],
        data: ['"SF Mono"', '"Cascadia Code"', 'Consolas', '"Liberation Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
};
