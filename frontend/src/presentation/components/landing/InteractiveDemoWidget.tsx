import { useEffect, useState } from 'react'
import { AUTO_DEMO_PRESET, type DemoPreset } from '@/domain/landing/demoPresets'

function nodeCenter(node: DemoPreset['nodes'][number]) {
  return { x: node.x + 70, y: node.y + 28 }
}

function buildPath(preset: DemoPreset, fromId: string, toId: string): string {
  const from = preset.nodes.find((n) => n.id === fromId)
  const to = preset.nodes.find((n) => n.id === toId)
  if (!from || !to) return ''
  const a = nodeCenter(from)
  const b = nodeCenter(to)
  const midX = (a.x + b.x) / 2
  return `M ${a.x} ${a.y} C ${midX} ${a.y}, ${midX} ${b.y}, ${b.x} ${b.y}`
}

export function InteractiveDemoWidget() {
  const preset = AUTO_DEMO_PRESET
  const [activeNodeId, setActiveNodeId] = useState(preset.animationPath[0])
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(() => {
      setTick((value) => {
        const next = (value + 1) % preset.animationPath.length
        setActiveNodeId(preset.animationPath[next])
        return next
      })
    }, 1200)
    return () => window.clearInterval(timer)
  }, [preset])

  const activeEdgeIndex = tick % preset.edges.length
  const activeNode = preset.nodes.find((node) => node.id === activeNodeId)

  return (
    <div className="demo-widget">
      <div className="demo-widget__canvas">
        <svg viewBox="0 0 760 200" className="demo-graph" aria-hidden>
          <defs>
            <linearGradient id="demo-edge-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#6366f1" />
              <stop offset="100%" stopColor="#a855f7" />
            </linearGradient>
            <filter id="demo-glow">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {preset.edges.map((edge, index) => {
            const path = buildPath(preset, edge.from, edge.to)
            const active = index === activeEdgeIndex
            return (
              <g key={edge.id}>
                <path
                  d={path}
                  className={`demo-edge${edge.loop ? ' demo-edge--loop' : ''}${active ? ' demo-edge--active' : ''}`}
                  fill="none"
                />
                {active && (
                  <circle r="4" className="demo-pulse-dot">
                    <animateMotion dur="1.1s" repeatCount="indefinite" path={path} />
                  </circle>
                )}
              </g>
            )
          })}

          {preset.nodes.map((node) => {
            const active = node.id === activeNodeId
            return (
              <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
                <rect
                  width="140"
                  height="56"
                  rx="12"
                  className={`demo-node${active ? ' demo-node--active' : ''}`}
                />
                <text x="12" y="22" className="demo-node__label">
                  {node.label}
                </text>
                <text x="12" y="40" className="demo-node__role">
                  {node.role}
                </text>
              </g>
            )
          })}
        </svg>

        <div className="demo-widget__caption">
          <strong>{preset.title}</strong>
          <span className="hint">
            Сейчас работает: <span className="demo-widget__active-agent">{activeNode?.label ?? '—'}</span>
            {' · '}
            {preset.description}
          </span>
        </div>
      </div>
    </div>
  )
}
