import { useState, type ReactElement } from 'react'
import {
  RESULT_PREVIEW_TABS,
  type ResultPreviewTab,
} from '@/domain/landing/demoPresets'
import {
  RESULT_CODE_META,
  RESULT_CODE_SAMPLE,
  RESULT_DIAGRAM_TABS,
  RESULT_DOCX_BODY,
  RESULT_DOCX_TITLE,
  type ResultDiagramTab,
} from '@/domain/landing/resultPreviewContent'
import { AppIcon } from '@/presentation/icons'
import { FlowchartDiagramPreview } from './result-preview/FlowchartDiagramPreview'
import { Idef0DiagramPreview } from './result-preview/Idef0DiagramPreview'
import { UmlDiagramPreview } from './result-preview/UmlDiagramPreview'

function DocxPreview() {
  return (
    <div className="result-preview__docx">
      <div className="result-preview__docx-page result-preview__docx-page--title">
        <p className="result-preview__docx-uni">{RESULT_DOCX_TITLE.university}</p>
        <p className="result-preview__docx-uni">{RESULT_DOCX_TITLE.institution}</p>
        <p className="result-preview__docx-uni">{RESULT_DOCX_TITLE.shortName}</p>
        <h4>{RESULT_DOCX_TITLE.type}</h4>
        <p className="result-preview__docx-topic">{RESULT_DOCX_TITLE.discipline}</p>
        <p className="result-preview__docx-topic">{RESULT_DOCX_TITLE.topic}</p>
        <div className="result-preview__docx-meta">
          <span>{RESULT_DOCX_TITLE.student}</span>
          <span>{RESULT_DOCX_TITLE.supervisor}</span>
          <span>{RESULT_DOCX_TITLE.cityYear}</span>
        </div>
      </div>

      <div className="result-preview__docx-page result-preview__docx-page--body">
        {RESULT_DOCX_BODY.sections.map((section) => (
          <section key={section.title} className="result-preview__docx-section">
            <h5>{section.title}</h5>
            {section.paragraphs.map((paragraph) => (
              <p key={paragraph.slice(0, 40)}>{paragraph}</p>
            ))}
            {'figure' in section && section.figure && (
              <p className="result-preview__docx-figure">{section.figure}</p>
            )}
          </section>
        ))}

        <section className="result-preview__docx-section result-preview__docx-section--bib">
          <h5>Список литературы</h5>
          <ol>
            {RESULT_DOCX_BODY.bibliography.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </section>
      </div>
    </div>
  )
}

function CodePreview() {
  return (
    <div className="result-preview__code">
      <div className="result-preview__code-header">
        <span>{RESULT_CODE_META.filename}</span>
        <span className="hint">{RESULT_CODE_META.status}</span>
      </div>
      <pre className="result-preview__code-block">{RESULT_CODE_SAMPLE}</pre>
      <pre className="result-preview__code-output">{RESULT_CODE_META.output}</pre>
    </div>
  )
}

const DIAGRAM_CONTENT: Record<ResultDiagramTab, () => ReactElement> = {
  idef0: Idef0DiagramPreview,
  uml: UmlDiagramPreview,
  flowchart: FlowchartDiagramPreview,
}

function DiagramPreview() {
  const [diagramTab, setDiagramTab] = useState<ResultDiagramTab>('idef0')
  const Diagram = DIAGRAM_CONTENT[diagramTab]

  return (
    <div className="result-preview__diagrams">
      <div className="result-preview__diagram-tabs" role="tablist" aria-label="Типы диаграмм">
        {RESULT_DIAGRAM_TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={diagramTab === item.id}
            className={`result-preview__diagram-tab${diagramTab === item.id ? ' result-preview__diagram-tab--active' : ''}`}
            onClick={() => setDiagramTab(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <Diagram />
    </div>
  )
}

const PREVIEW_CONTENT: Record<ResultPreviewTab, () => ReactElement> = {
  docx: DocxPreview,
  code: CodePreview,
  diagram: DiagramPreview,
}

export function ResultPreviewSection() {
  const [tab, setTab] = useState<ResultPreviewTab>('docx')
  const Preview = PREVIEW_CONTENT[tab]

  return (
    <section className="landing-section landing-result-preview" id="result">
      <div className="landing-section__head landing-section__head--center">
        <p className="landing-eyebrow">Результат</p>
        <h2>Что получаете на выходе</h2>
        <p className="landing-section__lead">
          Полноценная курсовая: оформленный docx, рабочий код с бенчмарками и профессиональные
          диаграммы IDEF0, UML и блок-схемы — готовые к сдаче.
        </p>
      </div>

      <div className="result-preview">
        <div className="result-preview__tabs" role="tablist" aria-label="Примеры результата">
          {RESULT_PREVIEW_TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={tab === item.id}
              className={`result-preview__tab${tab === item.id ? ' result-preview__tab--active' : ''}`}
              onClick={() => setTab(item.id)}
            >
              <AppIcon name={item.icon} size={16} />
              {item.label}
            </button>
          ))}
        </div>

        <div className="result-preview__panel" role="tabpanel">
          <Preview />
        </div>
      </div>
    </section>
  )
}
