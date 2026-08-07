import type { GraphTopologyDto } from '@/domain/graph/types'

const API = ''

export async function fetchGraphTopology(
  workType: string,
  pipeline?: string[],
): Promise<GraphTopologyDto> {
  const params = new URLSearchParams({ work_type: workType })
  if (pipeline?.length) {
    params.set('pipeline', JSON.stringify(pipeline))
  }
  const res = await fetch(`${API}/api/graph/topology?${params}`)
  if (!res.ok) throw new Error('Не удалось загрузить топологию графа')
  return res.json() as Promise<GraphTopologyDto>
}
