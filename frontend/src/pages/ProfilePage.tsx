import { isAxiosError } from 'axios'
import { UserX } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Tabs } from '@/components/ui/Tabs'
import { PostFeed } from '@/features/posts/components/PostFeed'
import { EditProfileSheet } from '@/features/profile/components/EditProfileSheet'
import { ProfileHeader } from '@/features/profile/components/ProfileHeader'
import { ProfileInfo } from '@/features/profile/components/ProfileInfo'
import { ProfilePeople } from '@/features/profile/components/ProfilePeople'
import { ProfilePhotos } from '@/features/profile/components/ProfilePhotos'
import { ProfileSkeleton } from '@/features/profile/components/ProfileSkeleton'
import { useProfile } from '@/features/profile/hooks/useProfile'
import { useDocumentTitle } from '@/hooks/useDocumentTitle'

const TABS = [
  { value: 'all', label: 'Todo' },
  { value: 'info', label: 'Información' },
  { value: 'people', label: 'Seguidores' },
  { value: 'photos', label: 'Fotos' },
] as const
type Tab = (typeof TABS)[number]['value']

/**
 * /profile (mío) y /profile/:userId. Sin menú lateral en escritorio (como Facebook): usa todo el
 * contenedor. La pestaña va en la URL (`?tab=`) para que se pueda compartir y volver con «atrás».
 */
export function ProfilePage() {
  const { userId } = useParams()
  const id = userId && /^\d+$/.test(userId) ? Number(userId) : undefined
  const profile = useProfile(id)
  const [params, setParams] = useSearchParams()
  const tab = (TABS.some((option) => option.value === params.get('tab')) ? params.get('tab') : 'all') as Tab
  const setTab = (next: Tab) => setParams(next === 'all' ? {} : { tab: next }, { replace: true })
  const [editing, setEditing] = useState(false)
  useDocumentTitle(profile.data?.name ?? 'Perfil')

  if (profile.isPending) return <ProfileSkeleton />
  if (profile.isError) {
    const notFound = isAxiosError(profile.error) && profile.error.response?.status === 404
    return (
      <Card>
        <EmptyState
          icon={UserX}
          title={notFound ? 'Este perfil no existe' : 'No se pudo cargar el perfil'}
          description={notFound ? 'Puede que la persona ya no forme parte de la empresa.' : 'Revisa tu conexión e inténtalo de nuevo.'}
          action={notFound ? <Link to="/people" className="text-sm font-semibold text-brand-600 hover:underline">Ir a Personas</Link> : <Button variant="outline" onClick={() => void profile.refetch()}>Reintentar</Button>}
        />
      </Card>
    )
  }

  const data = profile.data
  return (
    <div className="grid gap-4">
      <ProfileHeader profile={data} onEdit={() => setEditing(true)} onShowPeople={() => setTab('people')} />
      <Tabs label="Secciones del perfil" options={[...TABS]} value={tab} onChange={setTab} />

      {tab === 'all' && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] lg:items-start">
          <div className="grid gap-4 lg:sticky lg:top-20">
            <ProfileInfo profile={data} compact />
            <ProfilePhotos userId={data.id} preview onShowAll={() => setTab('photos')} />
          </div>
          <div className="min-w-0">
            <PostFeed filters={{ author: data.id }} emptyText={data.is_me ? 'Cuando publiques algo aparecerá aquí.' : 'Todavía no ha publicado nada.'} />
          </div>
        </div>
      )}
      {tab === 'info' && <ProfileInfo profile={data} />}
      {tab === 'people' && <ProfilePeople userId={data.id} />}
      {tab === 'photos' && <ProfilePhotos userId={data.id} />}

      {data.is_me && <EditProfileSheet key={data.bio} profile={data} open={editing} onOpenChange={setEditing} />}
    </div>
  )
}
