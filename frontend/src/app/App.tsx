import { useCallback, useState, type ReactNode } from 'react'
import { Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import { registerRecentJob, touchRecentJob } from '@/application/jobs/useRecentJobs'
import { useCreateJob, useHealthCheck, useServerFooter } from '@/application/jobs/useAppSession'
import { LandingPage } from '@/presentation/pages/LandingPage'
import { DashboardPage } from '@/presentation/pages/DashboardPage'
import { JobFormModal } from '@/presentation/components/job/JobFormModal'
import { WorkbenchPage } from '@/presentation/pages/WorkbenchPage'

const SESSION_KEY = 'aicursach_session_v1'

interface FormLaunch {
  title: string
  topic: string
  projectName: string
}

function WorkbenchRoute({ footer }: { footer: ReactNode }) {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()

  if (!jobId) {
    return <Navigate to="/app" replace />
  }

  return (
    <WorkbenchPage
      jobId={jobId}
      onNew={() => navigate('/app')}
      footer={footer}
    />
  )
}

function LegacyDashboardRedirect() {
  return <Navigate to="/app" replace />
}

function LegacyWorkbenchRedirect() {
  const { jobId } = useParams<{ jobId: string }>()
  if (!jobId) {
    return <Navigate to="/app" replace />
  }
  return <Navigate to={`/app/workbench/${jobId}`} replace />
}

export default function App() {
  const navigate = useNavigate()
  const health = useHealthCheck()
  const footerMeta = useServerFooter(health)
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => localStorage.getItem(SESSION_KEY) === '1',
  )
  const [formOpen, setFormOpen] = useState(false)
  const [formLaunch, setFormLaunch] = useState<FormLaunch>({
    title: 'Новый проект',
    topic: '',
    projectName: 'MyWork',
  })
  const [jobsRefresh, setJobsRefresh] = useState(0)

  const onJobCreated = useCallback(
    (jobId: string, form: FormData) => {
      registerRecentJob({
        id: jobId,
        projectName: String(form.get('project_name') || formLaunch.projectName),
        workType: 'auto',
        topic: String(form.get('topic') || formLaunch.topic),
      })
      setJobsRefresh((value) => value + 1)
      setFormOpen(false)
      navigate(`/app/workbench/${jobId}`)
    },
    [formLaunch.projectName, formLaunch.topic, navigate],
  )

  const { loading, error: formError, submit: handleSubmit, setError: setFormError } =
    useCreateJob(onJobCreated)

  const openForm = (launch: Partial<FormLaunch> & { title: string }) => {
    setFormLaunch({
      title: launch.title,
      topic: launch.topic ?? '',
      projectName: launch.projectName ?? 'MyWork',
    })
    setFormError('')
    setFormOpen(true)
  }

  const enterApp = () => {
    localStorage.setItem(SESSION_KEY, '1')
    setIsAuthenticated(true)
    navigate('/app')
  }

  const handleOpenJob = (id: string) => {
    touchRecentJob(id)
    navigate(`/app/workbench/${id}`)
  }

  const openNewProject = () =>
    openForm({
      title: 'Новый проект',
      topic: '',
      projectName: 'MyWork',
    })

  const footer = <span className={footerMeta.className}>{footerMeta.text}</span>

  const formModal = (
    <JobFormModal
      open={formOpen}
      title={formLaunch.title}
      loading={loading}
      error={formError}
      initialTopic={formLaunch.topic}
      initialProjectName={formLaunch.projectName}
      onClose={() => setFormOpen(false)}
      onSubmit={handleSubmit}
    />
  )

  return (
    <>
      <Routes>
        <Route
          path="/"
          element={
            <LandingPage
              health={health}
              isAuthenticated={isAuthenticated}
              onEnterApp={enterApp}
            />
          }
        />
        <Route
          path="/app"
          element={
            <>
              <DashboardPage
                refreshToken={jobsRefresh}
                onBackToMarketing={() => navigate('/')}
                onOpenJob={handleOpenJob}
                onCreateProject={openNewProject}
              />
              {formModal}
            </>
          }
        />
        <Route path="/app/workbench/:jobId" element={<WorkbenchRoute footer={footer} />} />
        <Route path="/dashboard" element={<LegacyDashboardRedirect />} />
        <Route path="/workbench/:jobId" element={<LegacyWorkbenchRedirect />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}
