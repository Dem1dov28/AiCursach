import { COMPARISON_ROWS } from '@/domain/landing/demoPresets'
import { AppIcon } from '@/presentation/icons'

function CellValue({ value }: { value: boolean | string }) {
  if (value === true) {
    return (
      <span className="compare-yes">
        <AppIcon name="check" size={16} strokeWidth={2.5} />
      </span>
    )
  }
  if (value === false) return <span className="compare-no">—</span>
  return <span className="compare-partial">{value}</span>
}

export function ComparisonSection() {
  return (
    <section className="landing-section landing-compare">
      <div className="landing-section__head landing-section__head--center">
        <p className="landing-eyebrow">Сравнение</p>
        <h2>Почему не просто ChatGPT?</h2>
        <p className="landing-section__lead">
          Рекурсивные циклы правок, Human-in-the-Loop и визуальный отладчик workflow — в одном
          продукте для учебных работ.
        </p>
      </div>

      <div className="compare-table-wrap">
        <table className="compare-table">
          <thead>
            <tr>
              <th>Возможность</th>
              <th>ChatGPT</th>
              <th>n8n</th>
              <th className="compare-table__ours">AiCursach</th>
            </tr>
          </thead>
          <tbody>
            {COMPARISON_ROWS.map((row) => (
              <tr key={row.feature}>
                <td>{row.feature}</td>
                <td>
                  <CellValue value={row.chatgpt} />
                </td>
                <td>
                  <CellValue value={row.n8n} />
                </td>
                <td className="compare-table__ours">
                  <CellValue value={row.ours} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
