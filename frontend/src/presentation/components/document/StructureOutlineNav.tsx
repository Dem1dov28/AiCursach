interface Props {
  outline: string
  onSelectLine?: (line: string) => void
}

/** Parse structure_outline into navigable chapter list. */
export function StructureOutlineNav({ outline, onSelectLine }: Props) {
  const lines = outline
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  if (lines.length === 0) return null

  return (
    <nav className="outline-nav" aria-label="Дерево плана">
      <h4 className="outline-nav__title">План документа</h4>
      <ul className="outline-nav__list">
        {lines.map((line, index) => (
          <li key={`${index}-${line.slice(0, 24)}`}>
            <button
              type="button"
              className="outline-nav__item"
              onClick={() => onSelectLine?.(line)}
              title={line}
            >
              {line}
            </button>
          </li>
        ))}
      </ul>
    </nav>
  )
}
