import { useEffect, useMemo, useRef } from 'react'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import type { JSONContent } from '@tiptap/core'
import { mapContentDraftToTiptap } from '@/domain/document/mapContentDraftToTiptap'
import type { CitationIssue, StyleIssue, WorkType } from '@/domain/jobs/types'
import { StyleIssuesPanel } from './StyleIssuesPanel'

interface Props {
  contentDraft?: string
  structureOutline?: string
  critiqueNotes?: string
  citationIssues?: CitationIssue[]
  styleIssues?: StyleIssue[]
  workType: WorkType
  truncated?: boolean
  writingActive?: boolean
  highlightQuery?: string
}

function docSignature(doc: JSONContent): string {
  return JSON.stringify(doc)
}

const EMPTY_DOC: JSONContent = {
  type: 'doc',
  content: [{ type: 'paragraph', content: [] }],
}

export function DocumentEditor({
  contentDraft,
  structureOutline,
  critiqueNotes,
  citationIssues,
  styleIssues,
  workType,
  truncated,
  writingActive,
  highlightQuery,
}: Props) {
  const lastApplied = useRef('')
  const isFocused = useRef(false)

  const documentContent = useMemo(
    () =>
      mapContentDraftToTiptap({
        contentDraft,
        structureOutline,
        critiqueNotes,
        workType,
      }),
    [contentDraft, structureOutline, critiqueNotes, workType],
  )

  const extensions = useMemo(() => [StarterKit], [])

  const editor = useEditor(
    {
      extensions,
      content: EMPTY_DOC,
      editable: true,
      shouldRerenderOnTransaction: false,
      editorProps: {
        attributes: {
          class: 'tiptap-surface',
        },
      },
      onFocus: () => {
        isFocused.current = true
      },
      onBlur: () => {
        isFocused.current = false
      },
    },
    [],
  )

  useEffect(() => {
    if (!editor || editor.isDestroyed) return
    const signature = docSignature(documentContent)
    if (signature === lastApplied.current) return
    if (isFocused.current && lastApplied.current) return

    try {
      editor.commands.setContent(documentContent, { emitUpdate: false })
      lastApplied.current = signature
    } catch {
      // Editor may be mid-teardown during tab switches or lazy unmount.
    }
  }, [editor, documentContent])

  const editorReady = editor && !editor.isDestroyed

  return (
    <div
      className={`document-editor${writingActive ? ' document-editor--writing' : ''}`}
      data-highlight={highlightQuery?.trim() || undefined}
    >
      {truncated && (
        <p className="hint document-editor__notice">
          Показана часть черновика — полный текст будет в итоговом docx.
        </p>
      )}
      {citationIssues && citationIssues.length > 0 && (
        <div className="citation-issues">
          <strong>Проблемы со сносками</strong>
          <ul>
            {citationIssues.map((issue) => (
              <li key={`${issue.citation}-${issue.reason}`}>
                {issue.citation}: {issue.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
      <StyleIssuesPanel issues={styleIssues ?? []} />
      {editorReady ? (
        <EditorContent editor={editor} />
      ) : (
        <p className="hint">Загрузка редактора…</p>
      )}
    </div>
  )
}
