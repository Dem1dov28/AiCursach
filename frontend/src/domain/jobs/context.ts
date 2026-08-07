export interface JobInputFile {
  kind: string
  filename: string
  size_bytes: number
  preview: string
  has_binary: boolean
}

export interface JobContext {
  job_id: string
  work_type: string
  project_name: string
  checkpointer: string
  inputs: JobInputFile[]
}

/** Nodes that can be manually restarted (mirrors backend domain). */
export const RERUN_NODE_IDS = [
  'researcher',
  'analyzer',
  'writer',
  'critiquer',
  'coder_gen',
  'code_runner',
  'diagrammer',
  'assets_builder',
  'antiplagiat',
  'annex_builder',
  'docx_builder',
] as const

export type RerunNodeId = (typeof RERUN_NODE_IDS)[number]

export function canRerunJob(status: string | undefined): boolean {
  return status === 'paused' || status === 'completed' || status === 'failed'
}
