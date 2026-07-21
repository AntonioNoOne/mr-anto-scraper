// Tailwind v2 — stessa versione delle classi usate nel markup, così il look
// resta identico. Purge attivo: tiene solo le classi realmente presenti in
// index.html e nei moduli JS, riducendo il CSS da ~qualche MB a pochi KB.
module.exports = {
  purge: {
    enabled: true,
    content: ['./index.html', './js/**/*.js'],
  },
  darkMode: false,
  theme: {
    extend: {},
  },
  variants: {
    extend: {},
  },
  plugins: [],
};
