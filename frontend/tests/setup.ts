import '@testing-library/jest-dom/vitest'

// jsdom does not implement FileReader for our purposes in every version; make
// sure matchMedia and scrollTo never blow up if a component touches them.
if (typeof window !== 'undefined') {
  window.matchMedia =
    window.matchMedia ??
    ((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => undefined,
      removeListener: () => undefined,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      dispatchEvent: () => false,
    }))
}
