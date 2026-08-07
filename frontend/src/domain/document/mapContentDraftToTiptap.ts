import type { JSONContent } from '@tiptap/core'
import type { WorkType } from '@/domain/jobs/types'

const LAB_SECTIONS: Array<{ key: string; title: string }> = [
  { key: 'purpose', title: 'Цель работы' },
  { key: 'theory', title: 'Теоретические сведения' },
  { key: 'variant_task', title: 'Задание варианта' },
  { key: 'program_code', title: 'Исходный код программы' },
  { key: 'program_work', title: 'Работа программы' },
  { key: 'conclusions', title: 'Выводы' },
]

function heading(level: number, text: string): JSONContent {
  return {
    type: 'heading',
    attrs: { level },
    content: [{ type: 'text', text }],
  }
}

function paragraph(text: string): JSONContent {
  return {
    type: 'paragraph',
    content: text ? [{ type: 'text', text }] : [],
  }
}

function textBlock(title: string, body: string): JSONContent[] {
  if (!body.trim()) return []
  return [heading(3, title), paragraph(body.trim())]
}

function parseDraft(raw: string): Record<string, unknown> | null {
  try {
    const data = JSON.parse(raw)
    return typeof data === 'object' && data !== null ? (data as Record<string, unknown>) : null
  } catch {
    return null
  }
}

function asString(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.filter((item) => typeof item === 'string').join('\n\n')
  return ''
}

function mapCourseworkDraft(data: Record<string, unknown>): JSONContent[] {
  const blocks: JSONContent[] = []

  const intro = data.intro
  if (Array.isArray(intro) && intro.length) {
    blocks.push(heading(2, 'Введение'))
    for (const part of intro) {
      if (typeof part === 'string' && part.trim()) blocks.push(paragraph(part.trim()))
    }
  }

  const sections = data.sections
  if (Array.isArray(sections)) {
    for (const section of sections) {
      if (!section || typeof section !== 'object') continue
      const record = section as Record<string, unknown>
      const title = asString(record.title)
      if (title) blocks.push(heading(2, title))
      const paragraphs = record.paragraphs
      if (Array.isArray(paragraphs)) {
        for (const part of paragraphs) {
          if (typeof part === 'string' && part.trim()) blocks.push(paragraph(part.trim()))
        }
      }
    }
  }

  const conclusion = data.conclusion
  if (Array.isArray(conclusion) && conclusion.length) {
    blocks.push(heading(2, 'Заключение'))
    for (const part of conclusion) {
      if (typeof part === 'string' && part.trim()) blocks.push(paragraph(part.trim()))
    }
  }

  const sources = data.sources
  if (Array.isArray(sources) && sources.length) {
    blocks.push(heading(2, 'Список литературы'))
    for (const source of sources) {
      if (typeof source === 'string' && source.trim()) blocks.push(paragraph(source.trim()))
    }
  }

  return blocks
}

function mapLabDraft(data: Record<string, unknown>): JSONContent[] {
  const blocks: JSONContent[] = []
  for (const section of LAB_SECTIONS) {
    blocks.push(...textBlock(section.title, asString(data[section.key])))
  }
  return blocks
}

/** Pure mapper: backend content_draft JSON → TipTap document. */
export function mapContentDraftToTiptap(input: {
  contentDraft?: string
  structureOutline?: string
  critiqueNotes?: string
  workType: WorkType
}): JSONContent {
  const content: JSONContent[] = []

  if (input.structureOutline?.trim()) {
    content.push(heading(2, 'Утверждённый план'))
    content.push(paragraph(input.structureOutline.trim()))
  }

  if (input.contentDraft?.trim()) {
    const parsed = parseDraft(input.contentDraft)
    if (parsed) {
      content.push(
        ...(input.workType === 'coursework'
          ? mapCourseworkDraft(parsed)
          : mapLabDraft(parsed)),
      )
    } else {
      content.push(heading(2, 'Черновик'))
      content.push(paragraph(input.contentDraft.trim()))
    }
  }

  if (input.critiqueNotes?.trim()) {
    content.push(heading(2, 'Замечания редактора'))
    content.push(paragraph(input.critiqueNotes.trim()))
  }

  if (!content.length) {
    content.push(
      paragraph('Документ появится после работы агентов Планировщика и Писателя.'),
    )
  }

  return { type: 'doc', content }
}
