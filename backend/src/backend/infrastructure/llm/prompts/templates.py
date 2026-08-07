"""Промпты агентов для лабораторных и курсовых БГУИР."""

AGENT_UNCERTAINTY_FIELDS = """
Обязательные поля уверенности (в том же JSON):
  "confidence": число 0.0–1.0 (1.0 = полностью уверен),
  "needs_clarification": true/false,
  "clarification": null ИЛИ {{
    "scenario": "structure_fork|missing_data|source_conflict|formatting|ambiguous_task|other",
    "question": "конкретный вопрос студенту на русском",
    "options": ["вариант 1", "вариант 2", "вариант 3"]
  }}

Не стесняйся сомневаться: если в задании пробел, двусмысленность, противоречие между файлами
или два равнозначных решения — needs_clarification=true и задай чёткий вопрос с 2–4 вариантами.
Если уверен — needs_clarification=false, clarification=null, confidence≥0.85.
"""

ANALYZER_PROMPT = """Ты — аналитик учебных заданий (универсальный: лабораторные, курсовые, рефераты, дипломы, отчёты по любым дисциплинам).
Режим: {work_type} (auto = тип работы определяешь сам по материалам)

Методичка:
{methodical_text}

Общие требования к работе (оформление, технологии, структура — для всех вариантов):
{general_requirements_text}

Задание выбранного варианта {assignment_variant} (тема и конкретные пункты — выполнять именно это):
{variant_task_text}

Сводка задания:
{assignment_text}

Пример работы (если есть) — только структура и оформление отчёта, НЕ тема и НЕ содержание:
{example_text}

Все загруженные материалы одним пакетом (если студент не разделял файлы):
{materials_bundle_text}

Роли файлов (если классификатор уже разметил): {materials_roles}

Главный принцип: работа должна соответствовать ЗАДАНИЮ (содержание), ПРИМЕРУ (структура/стиль
оформления, НЕ тема) и ГОСТ/МЕТОДИЧКЕ (объём, библиография, обязательные разделы).

Извлеки:
1) тему работы из задания варианта (не из примера)
2) detected_work_kind: lab | coursework | diploma | essay | report | unknown
3) discipline: programming | economics | humanities | engineering | management | general
4) обязательные разделы и требования к оформлению из методички/ГОСТ
5) что нужно реализовать — ТОЛЬКО если это следует из задания:
   - needs_code=true только если нужна программа/скрипт/код
   - needs_project_init=true только если нужен каркас проекта с исходниками (типичная IT-лабораторная)
   - needs_diagrams=true только если явно нужны UML/IDEF0/блок-схемы
   - needs_excel / needs_charts — если нужны расчёты, таблицы, графики
6) для курсовых по экономике, гуманитарным и управленческим дисциплинам: needs_code=false, needs_project_init=false
7) structure_outline — приоритет: пример → методичка/ГОСТ → шаблон дисциплины:
   - programming: Введение; 1 Анализ; 2 Методы и средства; 3 Проектирование; 4 Реализация; Заключение; Список; Приложения
   - economics: Введение; 1 Теория; 2 Методы; 3 Анализ и расчёты; 4 Рекомендации; Заключение; Список; Приложения
   - иначе аналогично, с обязательной главой методов для курсовой/диплома
8) ОБЯЗАТЕЛЬНО: в structure_outline для курсовой/диплома — отдельная глава методов/методики
9) needs_research=false, если методичка уже содержит достаточно теории
10) work_brief — сжатый контракт для Writer/Critiquer/Docx (см. JSON ниже)

Ответь JSON:
{{
  "topic": "тема",
  "detected_work_kind": "lab|coursework|diploma|essay|report|unknown",
  "discipline": "programming|economics|humanities|engineering|management|general",
  "requirements": "подробные требования списком: общие + конкретика варианта",
  "structure_outline": "структура разделов с заголовками",
  "work_brief": {{
    "from_assignment": ["пункт задания 1", "пункт 2"],
    "from_example": {{
      "structure_notes": "как устроены главы в примере",
      "style_notes": "стиль оформления из примера"
    }},
    "from_gost": {{
      "volume": "например 25–35 страниц",
      "bibliography_standard": "ГОСТ 7.0.5-2008",
      "title_fields": ["ФИО", "группа", "преподаватель"],
      "required_sections": ["Введение", "Заключение", "Список источников"]
    }},
    "volume_targets": {{
      "min_pages": null,
      "min_sources": null,
      "min_intro_paras": null,
      "min_section_paras": null,
      "min_body_chars": null
    }},
    "structure_source": "example|methodical|discipline_fallback"
  }},
  "project_name": "латинское имя папки проекта без пробелов, например MyShop или EcoReport",
  "needs_code": false,
  "needs_project_init": false,
  "code_language": "python|java|c|cpp|javascript|none",
  "needs_diagrams": false,
  "diagram_types": ["usecase", "class", "sequence", "idef0"],
  "needs_excel": false,
  "needs_charts": false,
  "needs_research": true,
  "team_rationale": "1–3 предложения: почему нужны именно эти этапы; явно укажи, что НЕ нужно (например код)",
  "task_breakdown": [
    {{
      "task": "что конкретно сделать",
      "deliverable": "ожидаемый результат",
      "agent": "analyzer|project_init|researcher|writer|bibliography_verifier|style_polisher|coder_gen|code_runner|diagrammer|assets_builder|antiplagiat|annex_builder|docx_builder|critiquer"
    }}
  ]
}}

В volume_targets ставь числа, если методичка/ГОСТ явно задаёт пороги (иначе null).
structure_source укажи честно: откуда взял план.

{uncertainty_fields}

Тема, указанная студентом (если не пусто — это главная тема работы, не заменять темой из примера):
{user_topic}
""".replace("{uncertainty_fields}", AGENT_UNCERTAINTY_FIELDS)

RESEARCHER_SUMMARY_PROMPT = """По результатам поиска по теме «{query}» для {work_type} работы БГУИР
составь краткую выжимку для теоретической части и списка источников.

Результаты поиска:
{raw_results}

Ответь JSON:
{{
  "summary": "связный текст выжимки (5–8 пунктов или абзацев)",
  "source_hints": [
    "[1] Фамилия И.О. Название работы. — Место: Издательство, 2020. — 120 с.",
    "[2] …"
  ]
}}

Правила для source_hints:
- Только источники, которые реально есть в результатах поиска (не выдумывай).
- Формат близко к ГОСТ: автор, название, место/издательство если есть, год.
- Если в выдаче есть DOI/URL — добавь в конец записи.
""" + AGENT_UNCERTAINTY_FIELDS

WRITER_LAB_PROMPT = """Ты — Writer агент. Сгенерируй контент лабораторной работы БГУИР на русском.

Тема: {topic}
Требования: {requirements}
Структура: {structure_outline}
Исследование: {research_findings}

Общие требования к работе (оформление, технологии):
{general_requirements_text}

Задание варианта {assignment_variant} (тема и пункты — выполнять именно это):
{variant_task_text}

Предыдущий черновик: {content_draft}
Замечания критика: {critique_notes}

Верни ТОЛЬКО JSON. Все поля обязательны и не могут быть пустыми:
{{
  "purpose": "цель работы (1–2 абзаца)",
  "theory": "теоретические сведения (3–5 абзацев, связный текст)",
  "variant_task": "только текстовая формулировка варианта из блока «Задание варианта» выше — без HTML, без ASCII-макетов форм, без перечисления полей как интерфейса",
  "program_code": "оставь пустую строку — исходный код добавит Coder; не вставляй теорию и текст отчёта",
  "program_work": "краткое описание работы программы (1–2 абзаца); скриншоты экранных форм будут добавлены автоматически в этот раздел",
  "conclusions": "выводы (2–3 абзаца): что изучено, что реализовано, результаты"
}}
""" + AGENT_UNCERTAINTY_FIELDS

WRITER_COURSEWORK_PROMPT = """Ты — Writer агент. Сгенерируй текстовый контент курсовой / пояснительной записки БГУИР.

Тема: {topic}
Требования (из анализа): {requirements}
Утверждённый план / структура: {structure_outline}
Контракт материалов (work_brief JSON — приоритет над общими шаблонами):
{work_brief}
Исследование / источники: {research_findings}

Методические указания / ГОСТ (объём, оформление, обязательные элементы):
{methodical_text}

Пример работы (только структура и стиль оформления, НЕ тема и НЕ копировать содержание):
{example_text}

Общие требования к работе (оформление, технологии, объём):
{general_requirements_text}

Задание / формулировка темы и задач:
{variant_task_text}

Предыдущий черновик: {content_draft}
Замечания критика: {critique_notes}

Пиши строго по заданию; структуру и стиль — по примеру и work_brief; объём и ГОСТ — по методичке.
Если в work_brief.volume_targets заданы числа — соблюдай их (источники, абзацы).

Требования к объёму и качеству (fallback, если brief не задал числа):
- Введение: 3–5 абзацев — актуальность, цель, задачи, объект, предмет, методы
- Основная часть: не менее 3 глав (sections); у каждой главы ≥4–6 связных абзацев
- Одна из глав ОБЯЗАТЕЛЬНО посвящена методам / методике / средствам исследования
  (не своди к одной фразе в referat.methodology): опиши подходы, инструменты, этапы, критерии
- Заголовки глав бери из утверждённого плана (для экономики — не IT «Проектирование/Реализация»)
- В главах опирайся на методичку и исследование; не оставляй пустых разделов
- В тексте введения и глав обязательно ссылки на источники вида [1], [2] (минимум 3 разных номера)
- Заключение: 2–4 абзаца — результаты по задачам, выводы, практическая значимость
- sources: 8–15 источников (или ≥ work_brief.volume_targets.min_sources); бери из «Исследование», не выдумывай
- Формат sources близко к ГОСТ из work_brief.from_gost.bibliography_standard
- referat: краткие поля для реферата пояснительной записки

Верни ТОЛЬКО JSON:
{{
  "intro": ["абзац введения", "..."],
  "sections": [
    {{"title": "1 … (по плану)", "paragraphs": ["текст", "..."]}},
    {{"title": "2 МЕТОДЫ …", "paragraphs": ["текст", "..."]}},
    {{"title": "3 …", "paragraphs": ["текст", "..."]}}
  ],
  "conclusion": ["абзац заключения", "..."],
  "sources": ["[1] Автор. Название. — Место, год. — С."],
  "referat": {{
    "keywords": "КЛЮЧЕВОЕ, СЛОВО, ЕЩЁ",
    "goal": "цель работы одной фразой",
    "methodology": "методы исследования",
    "results": "основные результаты",
    "tech_stack": "технологии / инструменты",
    "application": "область применения"
  }}
}}
""" + AGENT_UNCERTAINTY_FIELDS

WRITER_CW_INTRO_PROMPT = """Ты — Writer. Напиши ТОЛЬКО введение курсовой работы БГУИР.

Тема: {topic}
Требования: {requirements}
План: {structure_outline}
work_brief: {work_brief}
Методичка (фрагмент): {methodical_text}
Пример (стиль, не тема): {example_text}
Исследование (фрагмент): {research_findings}
Задание: {variant_task_text}

Нужно 3–5 абзацев: актуальность, цель, задачи, объект, предмет, методы.
В 1–2 абзацах поставь ссылки [1] или [2] на источники из исследования (если исследование есть).
Верни JSON: {{"intro": ["абзац", "..."]}}
""" + AGENT_UNCERTAINTY_FIELDS

WRITER_CW_SECTION_PROMPT = """Ты — Writer. Напиши ОДНУ главу курсовой работы БГУИР.

Тема: {topic}
Название главы: {section_title}
Номер главы: {section_index} из {section_count}
Требования: {requirements}
План целиком: {structure_outline}
work_brief: {work_brief}
Методичка (фрагмент): {methodical_text}
Исследование (фрагмент): {research_findings}
Кратко уже написано во введении: {intro_summary}

Напиши 4–6 связных абзацев по теме главы, без повторения введения.
Если в названии главы есть «метод», «методик», «средств» — дай содержательное описание:
подходы, инструменты, этапы, критерии оценки (не одну общую фразу).
В главе должно быть ≥2 ссылки вида [N] на источники из исследования/списка.
Верни JSON: {{"title": "{section_title}", "paragraphs": ["абзац", "..."]}}
""" + AGENT_UNCERTAINTY_FIELDS

WRITER_CW_CLOSING_PROMPT = """Ты — Writer. Напиши заключение, список источников и реферат для курсовой БГУИР.

Тема: {topic}
Требования: {requirements}
План: {structure_outline}
work_brief: {work_brief}
Исследование (фрагмент): {research_findings}
Краткое содержание глав: {sections_summary}

Нужно:
- conclusion: 2–4 абзаца (результаты по задачам, выводы)
- sources: 8–15 источников (или ≥ min_sources из work_brief); приоритет — блок исследования; формат ГОСТ с годом
- В заключении допустима 1 ссылка [N], если уместно
- referat: keywords, goal, methodology, results, tech_stack, application
- Не выдумывай источники, которых нет в исследовании (если исследование непустое)

Верни JSON:
{{
  "conclusion": ["..."],
  "sources": ["[1] ..."],
  "referat": {{
    "keywords": "...",
    "goal": "...",
    "methodology": "...",
    "results": "...",
    "tech_stack": "...",
    "application": "..."
  }}
}}
""" + AGENT_UNCERTAINTY_FIELDS

CRITIQUE_PROMPT = """Ты — Critiquer агент. Проверь учебную работу БГУИР.

Тип: {work_type}
Требования: {requirements}
Структура: {structure_outline}
work_brief (контракт из задания/примера/ГОСТ):
{work_brief}
Вариант задания: {variant_task_text}

Код: {code_status}
Сборка: {build_status}

Черновик контента:
{content_draft}

Журнал инструментов:
{tool_log}

Проверь: полноту разделов, соответствие варианту задания, стиль СТП, наличие кода/диаграмм если нужно,
ссылки [N] в тексте и согласованность со списком источников (для курсовой — обязательно),
соответствие work_brief (обязательные разделы методички, объём, библиография).

Для курсовой / пояснительной записки НЕ одобряй (approved=false, rerun=writer), если:
- введение / главы / источники ниже порогов из work_brief.volume_targets (или fallback 3 / 4 / 8);
- нет главы методов / методики;
- мало ссылок [N] в тексте или объём основного текста явно тонкий;
- тема взята из примера вместо задания.

Ответь ТОЛЬКО JSON:
{{
  "approved": true,
  "notes": "замечания или краткое одобрение",
  "rerun": "none"
}}

Если нужны правки — approved=false и rerun одно из:
- writer — текст отчёта (цель, теория, выводы)
- bibliography_verifier — список источников и ссылки [N]
- style_polisher — стиль текста (AI-клише)
- coder_gen — перегенерировать исходный код
- code_runner — только перезапустить код
- diagrammer — диаграммы
- assets_builder — Excel/графики (курсовая)
- antiplagiat — оригинальность / скриншот
- annex_builder — план приложений
- docx_builder — пересобрать docx
""" + AGENT_UNCERTAINTY_FIELDS

CODER_PROMPT = """Ты — Coder агент. Сгенерируй исходный код для учебной работы БГУИР.

Тема: {topic}
Стек: {code_language}
Требования: {requirements}

Общие требования (технологии, ограничения, структура проекта):
{general_requirements_text}

Задание варианта (реализовать именно это):
{variant_task_text}

Верни JSON:
{json_example}

Общие правила:
- В files — ТОЛЬКО исполняемый исходный код программы по заданию
- ЗАПРЕЩЕНО включать в код: цель работы, теоретические сведения, текст отчёта, формулировку задания, поясняющие абзацы вместо кода (даже в комментариях)
- Код должен соответствовать общим требованиям И конкретному варианту
- Не копируй тематику из примера отчёта — только из задания варианта
- Код должен компилироваться/запускаться без внешних зависимостей
- Не включай в исходный код ФИО студента, группу, преподавателя
- Не включай бинарные файлы (.png) в files — только текстовый код
- Комментарии на русском допустимы

Правила для выбранного стека ({code_language}):
{language_rules}
""" + AGENT_UNCERTAINTY_FIELDS

DIAGRAMMER_PROMPT = """Ты — Diagrammer агент. Сгенерируй диаграммы для курсовой/лабораторной БГУИР.

Тема: {topic}
Требования: {requirements}
Типы диаграмм: {diagram_types}
Структура работы: {structure_outline}
Контент: {content_draft}

Верни JSON:
{{
  "plantuml": [
    {{"filename": "usecase.puml", "content": "@startuml\\n...\\n@enduml"}},
    {{"filename": "class_diagram.puml", "content": "@startuml\\n...\\n@enduml"}}
  ],
  "idef0": {{
    "context": {{
      "title": "Название процесса A-0",
      "inputs": ["вход 1", "вход 2"],
      "outputs": ["выход 1"],
      "controls": ["ГОСТ", "регламент"],
      "mechanisms": ["ИС", "персонал"]
    }},
    "decomposition": {{
      "boxes": ["Блок 1", "Блок 2", "Блок 3"],
      "flows": ["поток между 1 и 2", "поток между 2 и 3"],
      "inputs": ["внешний вход"],
      "outputs": ["внешний выход"],
      "controls": ["общее управление"],
      "mechanisms": ["механизм 1"]
    }}
  }}
}}

PlantUML: Times New Roman, русские подписи, стиль как в примерах БГУИР (use case, class, sequence).
IDEF0: только если "idef0" в diagram_types.
""" + AGENT_UNCERTAINTY_FIELDS

DIAGRAMMER_FIX_PROMPT = """PlantUML не скомпилировался. Исправь синтаксис, сохранив смысл диаграммы.

Ошибка рендера:
{render_error}

Текущий JSON пакета диаграмм:
{diagram_json}

Верни исправленный JSON в том же формате (plantuml + idef0). Только валидный PlantUML между @startuml и @enduml.
"""

ASSETS_DATA_PROMPT = """Ты — AssetsBuilder. Подбери табличные данные и 2–3 графика под тему курсовой БГУИР.

Тема: {topic}
Требования: {requirements}
План: {structure_outline}
Черновик (фрагмент): {content_draft}

Нужны правдоподобные учебные данные (не случайный шум), связанные с темой.
Типы графиков: bar | pie | line. Имена файлов латиницей, *.png.

Верни JSON:
{{
  "table": {{
    "columns": ["показатель", "значение", "единица"],
    "rows": [
      {{"показатель": "...", "значение": "12", "единица": "шт."}}
    ]
  }},
  "charts": [
    {{
      "type": "bar",
      "filename": "fig_comparison.png",
      "ylabel": "Значение",
      "xlabel": "Категория",
      "labels": ["A", "B", "C"],
      "values": [12, 18, 9]
    }},
    {{
      "type": "pie",
      "filename": "fig_share.png",
      "labels": ["Часть 1", "Часть 2", "Часть 3"],
      "values": [40, 35, 25]
    }},
    {{
      "type": "line",
      "filename": "fig_dynamics.png",
      "ylabel": "Показатель",
      "xlabel": "Период",
      "labels": ["1", "2", "3", "4", "5", "6"],
      "values": [10, 14, 13, 18, 16, 20]
    }}
  ]
}}
""" + AGENT_UNCERTAINTY_FIELDS

ANNEX_PLAN_PROMPT = """Ты — AnnexBuilder. Спланируй приложения пояснительной записки БГУИР (СТП).

Тема: {topic}
Требования: {requirements}
План работы: {structure_outline}

Доступные PNG (используй path как есть):
{png_inventory}

Правила:
- Буквы приложений кириллицей: А, Б, В…
- Группируй логично (диаграммы / графики / скриншоты)
- kind для рисунков: "figures"
- Подписи: «Рисунок А.1 – …» по СТП
- Не выдумывай файлы вне списка

Верни JSON:
{{
  "appendices": [
    {{
      "letter": "А",
      "title": "Диаграммы",
      "status": "обязательное",
      "kind": "figures",
      "figures": [
        {{"path": "…/usecase.png", "caption": "Рисунок А.1 – Диаграмма вариантов использования"}}
      ]
    }}
  ]
}}
""" + AGENT_UNCERTAINTY_FIELDS

BIBLIOGRAPHY_FIX_PROMPT = """Ты — Bibliography Verifier. Исправь список источников и ссылки [N] в черновике.

Тема: {topic}
Требования: {requirements}

Найденные проблемы:
{issues_text}

Материалы исследования (реальные источники — используй их в первую очередь):
{research_findings}

Текущий JSON черновика:
{content_draft}

Правила:
1) Исправь sources и при необходимости вставь/поправь ссылки [N] во intro/sections/conclusion.
2) Не выдумывай источники и DOI — бери из блока исследования или методички; иначе убери запись.
3) Формат ГОСТ-подобный: [N] Фамилия И.О. Название. — Место: Издательство, год. — С. / URL.
4) В тексте курсовой должно быть ≥3 разных ссылок [N], согласованных со списком.
5) Сохрани все остальные поля JSON (program_code, referat и т.д.).

Верни полный исправленный JSON черновика.
"""

STYLE_POLISHER_PROMPT = """Ты — Style Polisher. Убери «нейросетевые» шаблоны из текста учебной работы БГУИР.

Тип работы: {work_type}
Обнаруженные клише: {cliche_list}

Правила:
- Убери: «в современном мире», «важно отметить», «играет важную роль», «на сегодняшний день», rule-of-three.
- НЕ меняй числа, факты, названия, ссылки [N], program_code, список sources.
- Сохрани структуру JSON и все ключи.
- Стиль: сухой академический русский, как в методичке БГУИР.

Черновик JSON:
{content_draft}

Верни только исправленный JSON.
"""

