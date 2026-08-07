import type { AutonomyLevel } from './types'

/** Map legacy API values to the two supported modes. */
export function normalizeAutonomyLevel(value?: string | null): AutonomyLevel {
  if (value === 'full_auto') return 'full_auto'
  return 'interactive'
}
