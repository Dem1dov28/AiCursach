import { AppHeader } from '@/presentation/components/app/AppHeader'
import { CreateProjectCard } from '@/presentation/components/dashboard/CreateProjectCard'
import { RecentProjectsTable } from '@/presentation/components/dashboard/RecentProjectsTable'
import { useRecentJobs } from '@/application/jobs/useRecentJobs'
import { useDashboardJobActions } from '@/application/jobs/useDashboardJobActions'

interface Props {
  refreshToken: number
  onBackToMarketing: () => void
  onOpenJob: (jobId: string) => void
  onCreateProject: () => void
}

export function DashboardPage({
  refreshToken,
  onBackToMarketing,
  onOpenJob,
  onCreateProject,
}: Props) {
  const { jobs, loading, error, reload } = useRecentJobs(refreshToken)
  const actions = useDashboardJobActions(reload)

  return (
    <div className="app-page">
      <AppHeader onBackToMarketing={onBackToMarketing} />

      <CreateProjectCard onStart={onCreateProject} />

      {(error || actions.error) && (
        <div className="alert alert-warn dashboard-list-error">{actions.error || error}</div>
      )}

      <RecentProjectsTable
        jobs={jobs}
        loading={loading}
        busyId={actions.busyId}
        onOpen={onOpenJob}
        onCreate={onCreateProject}
        onPause={actions.pause}
        onContinue={(job) => actions.continueJob(job, onOpenJob)}
        onDelete={actions.remove}
      />
    </div>
  )
}
