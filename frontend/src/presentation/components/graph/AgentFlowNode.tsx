import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import type { AgentFlowNodeData } from '@/application/graph/mapTopologyToFlow'
import { AppIcon } from '@/presentation/icons'
import { STATUS_LABELS } from '@/domain/graph/agentPresentation'

function AgentFlowNodeComponent({ data, selected }: NodeProps & { data: AgentFlowNodeData }) {
  const statusLabel = STATUS_LABELS[data.status] ?? data.status

  return (
    <div
      className={`agent-flow-node agent-flow-node--${data.status}${selected ? ' agent-flow-node--selected' : ''}`}
    >
      <span className="agent-flow-node__stripe" aria-hidden />
      <Handle type="target" position={Position.Top} className="agent-flow-handle" />

      <div className="agent-flow-node__top">
        <span className="agent-flow-node__icon" aria-hidden>
          <AppIcon name={data.iconName} size={18} />
        </span>
        <div className="agent-flow-node__titles">
          <span className="agent-flow-node__label">{data.displayLabel}</span>
          <span className="agent-flow-node__role">{data.role}</span>
        </div>
      </div>

      <div className="agent-flow-node__footer">
        <span className={`agent-flow-node__status agent-flow-node__status--${data.status}`}>
          {statusLabel}
        </span>
        {data.stepNumber != null && data.status === 'done' && (
          <span className="agent-flow-node__step">шаг {data.stepNumber}</span>
        )}
      </div>

      {data.miniLog && (
        <p className="agent-flow-node__log" title={data.miniLog}>
          {data.miniLog}
        </p>
      )}

      <Handle type="source" position={Position.Bottom} className="agent-flow-handle" />
    </div>
  )
}

export const AgentFlowNode = memo(AgentFlowNodeComponent)
