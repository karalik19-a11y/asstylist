/** Build stamp injected at Vite compile time (see vite.config.ts). */
declare const __ASSTYLIST_BUILD__: string

export const BUILD_STAMP: string =
  typeof __ASSTYLIST_BUILD__ !== 'undefined' && __ASSTYLIST_BUILD__
    ? __ASSTYLIST_BUILD__
    : 'dev'

export function formatBuildLabel(stamp: string = BUILD_STAMP): string {
  return `сборка ${stamp}`
}
