import type { ComponentType } from 'react'
import { createBrowserRouter, Outlet } from 'react-router'

import { pendingNav } from './navigation'

import { AppLayout } from '@/components/layout/AppLayout'
import { OfflineGate } from '@/components/feedback/OfflineGate'
import { OfflineScreen } from '@/components/feedback/OfflineScreen'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { RequireAccess } from '@/features/accounts/guards/RequireAccess'
import { GuestOnly } from '@/features/auth/guards/GuestOnly'
import { RequireAuth } from '@/features/auth/guards/RequireAuth'
import { ComingSoonPage } from '@/pages/ComingSoonPage'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/LoginPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { NotificationsPage } from '@/pages/NotificationsPage'
import { RouteErrorPage, ServerErrorPage } from '@/pages/ServerErrorPage'

/**
 * Página que se descarga al entrar a su ruta (su propio archivo .js): la app abre más rápido y cada sección
 * trae solo lo suyo. Si la descarga falla (sin red o tras publicar una versión nueva), el `errorElement`
 * de la raíz muestra «Sin conexión» o «Algo salió mal» con «Recargar».
 */
function page<K extends string>(load: () => Promise<Record<K, ComponentType>>, name: K) {
  return async () => ({ Component: (await load())[name] })
}

/** Solo en desarrollo: para ver las pantallas de error sin tener que provocarlas. */
const devErrorRoutes = import.meta.env.DEV
  ? [
      { path: '/dev/errors/404', element: <NotFoundPage /> },
      { path: '/dev/errors/500', lazy: page(() => import('@/pages/DevThrowErrorPage'), 'DevThrowErrorPage') },
      { path: '/dev/errors/500-static', element: <ServerErrorPage /> },
      { path: '/dev/errors/offline', element: <OfflineScreen /> },
    ]
  : []

/**
 * Todas las rutas en un solo lugar. Guard → layout → página.
 * Para agregar una sección: crear `pages/<Seccion>Page.tsx` y registrarla bajo `RequireAuth`.
 * Errores (404, 500 y sin conexión): a pantalla completa, centrados como el login, sin encabezado ni menú.
 * La raíz vigila la red (`OfflineGate`) y atrapa cualquier error al dibujar (`RouteErrorPage`).
 */
export const router = createBrowserRouter([
  {
    element: (
      <OfflineGate>
        <Outlet />
      </OfflineGate>
    ),
    errorElement: <RouteErrorPage />,
    children: [
      ...devErrorRoutes,
      // Sin sesión también: una ruta que no existe es 404 para todos («Ir al inicio» lleva al login si hace falta).
      { path: '*', element: <NotFoundPage /> },
      {
        element: <GuestOnly />,
        children: [{ element: <AuthLayout />, children: [{ path: '/login', element: <LoginPage /> }] }],
      },
      {
        element: <RequireAuth />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { index: true, element: <HomePage /> },
              { path: '/notifications', element: <NotificationsPage /> },
              { path: '/search', lazy: page(() => import('@/pages/SearchPage'), 'SearchPage') },
              // El perfil usa todo el contenedor, sin menú lateral (como Facebook).
              { path: '/profile', lazy: page(() => import('@/pages/ProfilePage'), 'ProfilePage'), handle: { fullWidth: true } },
              {
                element: <RequireAccess section="people" />,
                children: [
                  { path: '/calendar', lazy: page(() => import('@/pages/CalendarPage'), 'CalendarPage') },
                ],
              },
              {
                element: <RequireAccess section="blog" />,
                children: [
                  { path: '/blog', lazy: page(() => import('@/pages/BlogPage'), 'BlogPage') },
                  { path: '/blog/new', lazy: page(() => import('@/pages/ArticleEditorPage'), 'ArticleEditorPage') },
                  { path: '/blog/:articleId', lazy: page(() => import('@/pages/ArticlePage'), 'ArticlePage') },
                  { path: '/blog/:articleId/edit', lazy: page(() => import('@/pages/ArticleEditorPage'), 'ArticleEditorPage') },
                ],
              },
              {
                element: <RequireAccess section="documents" />,
                children: [
                  { path: '/documents', lazy: page(() => import('@/pages/DocumentsPage'), 'DocumentsPage') },
                  { path: '/documents/:documentId', lazy: page(() => import('@/pages/DocumentDetailPage'), 'DocumentDetailPage') },
                ],
              },
              {
                element: <RequireAccess section="forms" />,
                children: [
                  { path: '/forms', lazy: page(() => import('@/pages/FormsPage'), 'FormsPage') },
                  { path: '/forms/:formId', lazy: page(() => import('@/pages/FormPage'), 'FormPage') },
                  { path: '/forms/:formId/edit', lazy: page(() => import('@/pages/FormEditorPage'), 'FormEditorPage') },
                  { path: '/forms/:formId/results', lazy: page(() => import('@/pages/FormResultsPage'), 'FormResultsPage') },
                ],
              },
              {
                element: <RequireAccess section="helpdesk" />,
                children: [
                  { path: '/helpdesk', lazy: page(() => import('@/pages/HelpdeskPage'), 'HelpdeskPage') },
                  { path: '/helpdesk/:ticketId', lazy: page(() => import('@/pages/TicketPage'), 'TicketPage') },
                ],
              },
              {
                element: <RequireAccess section="marketplace" />,
                children: [
                  { path: '/marketplace', lazy: page(() => import('@/pages/MarketplacePage'), 'MarketplacePage') },
                  { path: '/marketplace/:listingId', lazy: page(() => import('@/pages/ListingPage'), 'ListingPage') },
                ],
              },
              {
                element: <RequireAccess section="posts" />,
                children: [
                  { path: '/posts/:postId', lazy: page(() => import('@/pages/PostDetailPage'), 'PostDetailPage') },
                ],
              },
              {
                element: <RequireAccess section="people" />,
                children: [
                  { path: '/people', lazy: page(() => import('@/pages/PeoplePage'), 'PeoplePage') },
                  { path: '/people/org', lazy: page(() => import('@/pages/PeoplePage'), 'PeoplePage') },
                  { path: '/profile/:userId', lazy: page(() => import('@/pages/ProfilePage'), 'ProfilePage'), handle: { fullWidth: true } },
                ],
              },
              // Secciones del menú sin pantalla todavía (app/navigation.ts → ready: false).
              ...pendingNav.map((item) => ({ path: item.to, element: <ComingSoonPage title={item.label} /> })),
            ],
          },
        ],
      },
    ],
  },
])
