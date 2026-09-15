// Deliberately empty: the app uses plain CSS (no Tailwind / PostCSS plugins).
// It also stops Vite from walking up parent folders and loading a stray
// postcss.config.* left behind by some other project.
module.exports = { plugins: {} };
