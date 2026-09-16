type DevilAProps = {
  className?: string
}

const LOGO_SRC = '/asstylist-logo.svg?brand=20260916-v6'

export function DevilA({ className }: DevilAProps) {
  return <img className={className ? `brand-logo-image ${className}` : 'brand-logo-image'} src={LOGO_SRC} alt="" aria-hidden="true" />
}
