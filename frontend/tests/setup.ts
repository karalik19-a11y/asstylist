import '@testing-library/jest-dom/vitest'

// jsdom does not implement FileReader for our purposes in every version; make
// sure matchMedia and scrollTo never blow up if a component touches them.
if (typeof window !== 'undefined') {
  // jsdom has no IntersectionObserver; provide a no-op stub for infinite scroll.
  if (typeof (window as unknown as { IntersectionObserver?: unknown }).IntersectionObserver === 'undefined') {
    class IntersectionObserverStub {
      observe() {}
      unobserve() {}
      disconnect() {}
      takeRecords() {
        return []
      }
    }
    ;(window as unknown as { IntersectionObserver: unknown }).IntersectionObserver = IntersectionObserverStub
    ;(globalThis as unknown as { IntersectionObserver: unknown }).IntersectionObserver = IntersectionObserverStub
  }

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
