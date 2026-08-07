import type { ReactNode } from 'react'

interface Props {
  left: ReactNode
  center: ReactNode
  right: ReactNode
  footer?: ReactNode
}

export function WorkbenchLayout({ left, center, right, footer }: Props) {
  return (
    <div className="workbench">
      <div className="workbench-grid">
        <aside className="workbench-left">{left}</aside>
        <main className="workbench-center">{center}</main>
        <aside className="workbench-right">{right}</aside>
      </div>

      {footer && <footer className="workbench-footer">{footer}</footer>}
    </div>
  )
}
