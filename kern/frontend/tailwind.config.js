export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      // Wie bei der Finanzapp: Farben als CSS-Variablen (siehe style.css), per .dark umgeschaltet statt per
      // Media-Query. Komponenten nutzen bg-primary/text-theme-inv/… statt dark:-Klassen nebenher zu pflegen.
      colors: {
        primary: 'var(--color-primary)',
        'primary-darker': 'var(--color-primary-darker)',
        theme: 'var(--color-theme)',
        'theme-inv': 'var(--color-theme-inv)',
        backdrop: 'var(--color-backdrop)',
        highlight: 'var(--color-highlight)',
        link: 'var(--color-link)',
        error: 'var(--color-error)',
        success: 'var(--color-success)',
      },
    },
  },
  plugins: [],
}
