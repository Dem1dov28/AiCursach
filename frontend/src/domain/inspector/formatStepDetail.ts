/** Hide redundant or overly technical step detail from the inspector UI. */
export function shouldShowStepDetail(detail?: string, message?: string): boolean {
  const text = detail?.trim()
  if (!text) return false
  if (text === message?.trim()) return false
  if (/^→\s*\w+/.test(text)) return false
  return true
}
