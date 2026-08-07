import { MarketingHeader } from '@/presentation/components/landing/MarketingHeader'
import { HeroSection } from '@/presentation/components/landing/HeroSection'
import { FeaturesSection } from '@/presentation/components/landing/FeaturesSection'
import { ComparisonSection } from '@/presentation/components/landing/ComparisonSection'
import { CtaSection } from '@/presentation/components/landing/CtaSection'
import { LandingFooter } from '@/presentation/components/landing/LandingFooter'
import { ProductPreviewSection } from '@/presentation/components/landing/ProductPreviewSection'
import { AgentGallerySection } from '@/presentation/components/landing/AgentGallerySection'
import { ResultPreviewSection } from '@/presentation/components/landing/ResultPreviewSection'
import { WorkflowSection } from '@/presentation/components/landing/WorkflowSection'
import { FaqSection } from '@/presentation/components/landing/FaqSection'
import type { Health } from '@/domain/jobs/types'

interface Props {
  health: Health | null
  isAuthenticated: boolean
  onEnterApp: () => void
}

export function LandingPage({ health, isAuthenticated, onEnterApp }: Props) {
  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="landing-page marketing-page">
      <MarketingHeader
        isAuthenticated={isAuthenticated}
        onEnterApp={onEnterApp}
      />

      <HeroSection
        onEnterApp={onEnterApp}
        onScrollToHow={() => scrollTo('how')}
      />

      <ProductPreviewSection />

      <FeaturesSection />

      <AgentGallerySection />

      <ResultPreviewSection />

      <WorkflowSection onEnterApp={onEnterApp} />

      <ComparisonSection />

      <FaqSection />

      <CtaSection onEnterApp={onEnterApp} />

      <LandingFooter health={health} />
    </div>
  )
}
