type DevilAProps = {
  className?: string
}

export function DevilA({ className }: DevilAProps) {
  return (
    <img
      className={className ? `brand-logo-image ${className}` : 'brand-logo-image'}
      src="/asstylist-logo.svg"
      alt=""
      aria-hidden="true"
    />
  )
}
