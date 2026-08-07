import type { Edge, Node } from '@xyflow/react'
import type { AgentFlowNodeData } from '@/application/graph/mapTopologyToFlow'

const Y_GAP = 128

function node(
  id: string,
  yIndex: number,
  data: AgentFlowNodeData,
  statusClass: string,
): Node<AgentFlowNodeData> {
  return {
    id,
    type: 'agent',
    position: { x: 400, y: yIndex * Y_GAP },
    data,
    className: statusClass,
  }
}

export const LANDING_WORKBENCH_NODES: Node<AgentFlowNodeData>[] = [
  node('supervisor', 0, {
    label: 'supervisor',
    displayLabel: 'Координатор',
    iconName: 'target',
    role: 'Маршрутизация',
    kind: 'supervisor',
    status: 'done',
    stepNumber: 1,
  }, 'flow-node-done'),
  node('analyzer', 1, {
    label: 'analyzer',
    displayLabel: 'Архитектор (план)',
    iconName: 'clipboard-list',
    role: 'План работы',
    kind: 'worker',
    status: 'done',
    stepNumber: 2,
  }, 'flow-node-done'),
  node('writer', 2, {
    label: 'writer',
    displayLabel: 'Писатель',
    iconName: 'pen-line',
    role: 'Глава 2',
    kind: 'worker',
    status: 'active',
    miniLog: 'Пишу раздел «Анализ алгоритмов»…',
  }, 'flow-node-active'),
  node('critiquer', 3, {
    label: 'critiquer',
    displayLabel: 'Редактор / критик',
    iconName: 'message-square',
    role: 'Правки',
    kind: 'worker',
    status: 'idle',
  }, 'flow-node-idle'),
  node('diagrammer', 4, {
    label: 'diagrammer',
    displayLabel: 'Диаграммы',
    iconName: 'network',
    role: 'UML-схема',
    kind: 'worker',
    status: 'idle',
  }, 'flow-node-idle'),
  node('docx_builder', 5, {
    label: 'docx_builder',
    displayLabel: 'Оформитель (docx)',
    iconName: 'file-text',
    role: 'Сборка docx',
    kind: 'worker',
    status: 'idle',
  }, 'flow-node-idle'),
]

export const LANDING_WORKBENCH_EDGES: Edge[] = [
  { id: 'e1', source: 'supervisor', target: 'analyzer', type: 'smoothstep' },
  { id: 'e2', source: 'analyzer', target: 'writer', type: 'smoothstep' },
  { id: 'e3', source: 'writer', target: 'critiquer', type: 'smoothstep' },
  { id: 'e4', source: 'critiquer', target: 'writer', type: 'smoothstep', label: 'цикл правок', labelStyle: { fill: '#fca5a5', fontSize: 10, fontWeight: 600 } },
  { id: 'e5', source: 'writer', target: 'diagrammer', type: 'smoothstep' },
  { id: 'e6', source: 'diagrammer', target: 'docx_builder', type: 'smoothstep' },
]

export const LANDING_WORKBENCH_ROSTER = [
  { id: 'supervisor', label: 'Координатор', status: 'done' as const },
  { id: 'analyzer', label: 'Архитектор (план)', status: 'done' as const },
  { id: 'writer', label: 'Писатель', status: 'active' as const },
  { id: 'critiquer', label: 'Редактор / критик', status: 'idle' as const },
  { id: 'diagrammer', label: 'Диаграммы', status: 'idle' as const },
  { id: 'docx_builder', label: 'Оформитель (docx)', status: 'idle' as const },
]

export const LANDING_WORKBENCH_DRAFT = `2. Анализ алгоритмов сортировки

Алгоритмы сортировки делятся на сравнительные и несравнительные. QuickSort в среднем случае показывает сложность O(n log n), однако в худшем случае деградирует до O(n²).

def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    mid = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + mid + quicksort(right)`
