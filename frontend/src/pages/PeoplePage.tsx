import { lazy, Suspense } from 'react'
import { useLocation, useNavigate } from 'react-router'

import { Skeleton } from '@/components/feedback/Skeleton'
import { PageHeader } from '@/components/layout/PageHeader'
import { Tabs } from '@/components/ui/Tabs'
import { NoAccess } from '@/features/accounts/guards/RequireAccess'
import { useSectionAccess } from '@/features/accounts/hooks/useCan'
import { PeopleDirectory } from '@/features/people/components/PeopleDirectory'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

// El organigrama (d3) pesa: se descarga solo al abrir su pestaña.
const OrgChartView = lazy(() => import('@/features/people/components/OrgChartView').then((module) => ({ default: module.OrgChartView })))

const TABS = [
  { value: 'directory', label: 'Directorio' },
  { value: 'org', label: 'Organigrama' },
] as const

/** /people (Directorio) y /people/org (Organigrama). */
export function PeoplePage() {
  const { pathname, search } = useLocation()
  const navigate = useNavigate()
  const tab = pathname.startsWith('/people/org') ? 'org' : 'directory'
  const { canSee } = useSectionAccess()
  const canSeeChart = canSee('orgChart')   // el organigrama tiene su propio permiso
  useDocumentTitle(tab === 'org' ? 'Organigrama' : 'Personas')

  return (
    <>
      <PageHeader title="Personas" description="Encuentra a tus compañeros y cómo está organizada la empresa." />
      <Tabs
        label="Secciones de Personas"
        options={TABS.filter((item) => item.value !== 'org' || canSeeChart)}
        value={tab}
        onChange={(next) => navigate(next === 'org' ? '/people/org' : `/people${search}`)}
        className="mb-4"
      />
      {tab === 'directory' ? (
        <PeopleDirectory />
      ) : !canSeeChart ? (
        <NoAccess />
      ) : (
        <Suspense fallback={<Skeleton className="h-[min(70dvh,44rem)] min-h-96 w-full rounded-2xl" />}>
          <OrgChartView />
        </Suspense>
      )}
    </>
  )
}
