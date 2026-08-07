import type { AppIconName } from '@/domain/icons/types'

export type DemoPresetId = 'auto'

export interface DemoNode {
  id: string
  label: string
  role: string
  x: number
  y: number
}

export interface DemoEdge {
  id: string
  from: string
  to: string
  loop?: boolean
}

export interface DemoPreset {
  id: DemoPresetId
  title: string
  description: string
  nodes: DemoNode[]
  edges: DemoEdge[]
  /** Node ids visited in animation loop */
  animationPath: string[]
}

export const AUTO_DEMO_PRESET: DemoPreset = {
  id: 'auto',
  title: 'Живой граф выполнения',
  description: 'Writer ↔ Редактор — цикл правок, пока текст не пройдёт проверку',
  nodes: [
    { id: 'supervisor', label: 'Координатор', role: 'supervisor', x: 24, y: 72 },
    { id: 'analyzer', label: 'Архитектор', role: 'analyzer', x: 168, y: 72 },
    { id: 'writer', label: 'Писатель', role: 'writer', x: 312, y: 32 },
    { id: 'critiquer', label: 'Редактор', role: 'critiquer', x: 312, y: 112 },
    { id: 'diagrammer', label: 'Диаграммы', role: 'diagrammer', x: 456, y: 72 },
    { id: 'docx_builder', label: 'Docx', role: 'docx_builder', x: 600, y: 72 },
  ],
  edges: [
    { id: 'e1', from: 'supervisor', to: 'analyzer' },
    { id: 'e2', from: 'analyzer', to: 'writer' },
    { id: 'e3', from: 'writer', to: 'critiquer' },
    { id: 'e4', from: 'critiquer', to: 'writer', loop: true },
    { id: 'e5', from: 'writer', to: 'diagrammer' },
    { id: 'e6', from: 'diagrammer', to: 'docx_builder' },
  ],
  animationPath: ['supervisor', 'analyzer', 'writer', 'critiquer', 'writer', 'diagrammer', 'docx_builder'],
}

/** Hero metrics shown under primary CTA. */
export const HERO_STATS = [
  { value: '12+', label: 'агентов в команде' },
  { value: 'Docx / LaTeX', label: 'готовый экспорт' },
  { value: 'Пауза', label: 'на плане и правках' },
] as const

/** Static agent cards for landing gallery (stage 2). */
export const AGENT_SHOWCASE: ReadonlyArray<{
  id: string
  icon: AppIconName
  title: string
  text: string
}> = [
  { id: 'supervisor', icon: 'target', title: 'Координатор', text: 'Маршрутизирует задачи и следит за прогрессом всей команды.' },
  { id: 'analyzer', icon: 'clipboard-list', title: 'Архитектор', text: 'Разбирает задание, определяет тип работы и строит план.' },
  { id: 'researcher', icon: 'search', title: 'Исследователь', text: 'Ищет источники и формирует базу для списка литературы.' },
  { id: 'writer', icon: 'pen-line', title: 'Писатель', text: 'Пишет текст разделов по структуре и методичке.' },
  { id: 'coder_gen', icon: 'code', title: 'Генерация кода', text: 'Пишет и адаптирует код для лабораторных работ.' },
  { id: 'code_runner', icon: 'play', title: 'Запуск кода', text: 'Проверяет, что программа запускается и даёт результат.' },
  { id: 'diagrammer', icon: 'network', title: 'Диаграммы', text: 'Строит UML, блок-схемы и схемы для отчёта.' },
  { id: 'critiquer', icon: 'message-square', title: 'Редактор', text: 'Проверяет текст и возвращает на доработку в цикле правок.' },
  { id: 'bibliography_verifier', icon: 'library', title: 'Библиография', text: 'Верифицирует DOI и оформление списка источников.' },
  { id: 'assets_builder', icon: 'bar-chart', title: 'Excel / графики', text: 'Готовит таблицы и графики для приложений.' },
  { id: 'antiplagiat', icon: 'check-circle', title: 'Антиплагиат', text: 'Вшивает % оригинальности и скриншот отчёта в приложение А.' },
  { id: 'annex_builder', icon: 'folder', title: 'Приложения', text: 'Планирует буквы приложений и подписи к рисункам.' },
  { id: 'style_polisher', icon: 'sparkles', title: 'Стиль', text: 'Выравнивает тон и убирает типичные следы ИИ-текста.' },
  { id: 'docx_builder', icon: 'file-text', title: 'Оформитель', text: 'Собирает финальный docx с титулом, оглавлением и рисунками.' },
]

export const FEATURE_CARDS: ReadonlyArray<{
  icon: AppIconName
  title: string
  text: string
}> = [
  {
    icon: 'hexagon',
    title: 'Команда агентов',
    text: 'Supervisor маршрутизирует задачи между Analyzer, Writer, CoderGen, Diagrammer и другими специалистами.',
  },
  {
    icon: 'hand',
    title: 'Human-in-the-Loop',
    text: 'Пауза на утверждении плана, уточняющие вопросы и согласование состава команды — вы контролируете процесс.',
  },
  {
    icon: 'file-text',
    title: 'Экспорт docx',
    text: 'Готовый docx с титулом, оглавлением, рисунками и списком литературы — по шаблону вашего вуза.',
  },
  {
    icon: 'git-branch',
    title: 'Живой граф workflow',
    text: 'Смотрите, какой агент работает сейчас, где цикл Writer ↔ Reviewer и куда пойдёт поток дальше.',
  },
  {
    icon: 'history',
    title: 'Checkpoint & diff',
    text: 'Откат к сохранённому состоянию и сравнение версий черновика — как time travel для документа.',
  },
  {
    icon: 'library',
    title: 'Библиография',
    text: 'Проверка DOI через CrossRef, отчёт по цитированию и верификация списка источников.',
  },
]

export const COMPARISON_ROWS = [
  {
    feature: 'Визуальный граф агентов',
    chatgpt: false,
    n8n: 'Частично',
    ours: true,
  },
  {
    feature: 'Рекурсивные циклы Writer ↔ Reviewer',
    chatgpt: false,
    n8n: 'Вручную',
    ours: true,
  },
  {
    feature: 'Human-in-the-Loop (пауза на плане)',
    chatgpt: false,
    n8n: 'Webhook',
    ours: true,
  },
  {
    feature: 'Time travel по checkpoint',
    chatgpt: false,
    n8n: false,
    ours: true,
  },
  {
    feature: 'Экспорт docx / LaTeX по ГОСТ',
    chatgpt: 'Копипаст',
    n8n: 'Скрипты',
    ours: true,
  },
] as const

export const HOW_IT_WORKS_STEPS = [
  {
    step: 1,
    title: 'Загрузите материалы',
    text: 'Задание, методичка, пример — Planner сам определит тип работы и соберёт команду агентов.',
  },
  {
    step: 2,
    title: 'Согласуйте план',
    text: 'Supervisor определит формат работы, соберёт команду агентов и покажет план — вы подтверждаете или уточняете.',
  },
  {
    step: 3,
    title: 'Получите готовый документ',
    text: 'Экспортируйте файл по ГОСТу с источниками, кодом и диаграммами.',
  },
] as const

/** Combined auto-mode + process timeline for landing. */
export const WORKFLOW_STEPS = [
  {
    step: 1,
    title: 'Загрузите материалы',
    text: 'Задание, методичка и пример отчёта — всё в одном проекте.',
  },
  {
    step: 2,
    title: 'Авторежим определит формат',
    text: 'Система поймёт: лабораторная или курсовая, нужен ли код, диаграммы и Excel.',
    badge: 'Авторежим',
  },
  {
    step: 3,
    title: 'Согласуйте план',
    text: 'Координатор покажет команду агентов и план — вы подтверждаете или уточняете.',
  },
  {
    step: 4,
    title: 'Получите документ',
    text: 'Экспорт docx или LaTeX с источниками, кодом и иллюстрациями.',
  },
] as const

export type ResultPreviewTab = 'docx' | 'code' | 'diagram'

export const RESULT_PREVIEW_TABS: ReadonlyArray<{
  id: ResultPreviewTab
  label: string
  icon: AppIconName
}> = [
  { id: 'docx', label: 'Docx', icon: 'file-text' },
  { id: 'code', label: 'Код', icon: 'code' },
  { id: 'diagram', label: 'Диаграмма', icon: 'network' },
]

export const FAQ_ITEMS: ReadonlyArray<{ question: string; answer: string }> = [
  {
    question: 'Чем AiCursach отличается от ChatGPT?',
    answer:
      'ChatGPT — один универсальный чат. AiCursach — команда специализированных агентов с живым графом выполнения, циклами правок Writer ↔ Редактор, паузами на согласование и экспортом готового docx или LaTeX.',
  },
  {
    question: 'Какие работы поддерживаются?',
    answer:
      'Лабораторные и курсовые работы: текст, программный код, диаграммы, таблицы и Excel-графики. Тип работы определяется автоматически после загрузки задания и методички.',
  },
  {
    question: 'Можно ли контролировать процесс?',
    answer:
      'Да. Система останавливается на согласовании плана и состава команды агентов, задаёт уточняющие вопросы и позволяет поставить выполнение на паузу в любой момент.',
  },
  {
    question: 'Что получаю на выходе?',
    answer:
      'Готовый docx или LaTeX с титульным листом, оглавлением, текстом, кодом, диаграммами и списком литературы — оформленный по структуре вашей методички.',
  },
  {
    question: 'Сколько времени занимает?',
    answer:
      'Зависит от объёма и сложности работы. В приложении виден прогресс, активный агент и текущий этап — вы всегда понимаете, что происходит прямо сейчас.',
  },
  {
    question: 'Можно ли править текст?',
    answer:
      'Да. Черновик доступен в приложении, есть checkpoint — откат к сохранённой версии — и diff для сравнения изменений между итерациями.',
  },
  {
    question: 'Это бесплатно?',
    answer:
      'Сейчас AiCursach в режиме BETA — попробовать можно бесплатно. Стоимость зависит от объёма работы и используемых моделей; расходы отображаются в метриках проекта.',
  },
]
