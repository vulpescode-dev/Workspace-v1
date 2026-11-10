import { useQuery } from '@tanstack/react-query'
import { OrgChart } from 'd3-org-chart'
import { zoomIdentity } from 'd3-zoom'
import { ChevronsDownUp, ChevronsUpDown, Maximize2, Network, Search, ZoomIn, ZoomOut } from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { useNavigate } from 'react-router'

import { EmptyState } from '@/components/feedback/EmptyState'
import { Skeleton } from '@/components/feedback/Skeleton'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { env } from '@/config/env'
import { cn } from '@/lib/cn'
import { getProtectedObjectUrl } from '@/lib/media/protected-files'

import { peopleApi, peopleKeys, type ChartNode } from '../api/people.api'

/** Fila plana que necesita d3-org-chart (un solo árbol: la empresa arriba, luego por jefe directo). */
interface Row {
  id: string
  parentId: string | null
  personId: number | null
  name: string
  initials: string
  jobTitle: string
  department: string
  reports: number
  photo: string | null
}

const ROOT_ID = 'empresa'
const MIN_READABLE_SCALE = 0.7
const NODE_WIDTH = 240
const NODE_HEIGHT = 112
const BRAND = '#0066cc'

/**
 * Organigrama por jefe directo (d3-org-chart 3.1.1, igual que la versión anterior). Tarjetas: foto ›
 * nombre (lleva al perfil) › cargo › área. Controles: Ajustar, Abrir todo, Cerrar, acercar/alejar y un
 * buscador que centra a la persona y resalta su cadena de mando.
 * Movimiento: la primera vista aparece sin animación y nunca más pequeña que 70 % (legible); abrir o
 * cerrar ramas anima 250 ms; con «reducir movimiento», nada se anima.
 */
export function OrgChartView() {
  const navigate = useNavigate()
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<OrgChart<Row> | null>(null)
  const [query, setQuery] = useState('')
  const chart = useQuery({ queryKey: peopleKeys.chart(), queryFn: () => peopleApi.chart(10), staleTime: 5 * 60_000 })

  // Las fotos piden sesión: se descargan (con caché) antes de dibujar; si alguna falla, quedan iniciales.
  const rows = useQuery({
    queryKey: [...peopleKeys.chart(), 'rows'],
    enabled: chart.isSuccess,
    staleTime: 5 * 60_000,
    queryFn: async () => {
      const flat = flatten(chart.data!.roots)
      await Promise.allSettled(flat.map(async (row) => {
        if (row.photo) row.photo = await getProtectedObjectUrl(row.photo).catch(() => null)
      }))
      return [companyRow(), ...flat]
    },
  })

  const people = useMemo(() => (rows.data ?? []).filter((row) => row.personId !== null), [rows.data])

  useEffect(() => {
    const container = containerRef.current
    if (!container || !rows.data || rows.data.length < 2) return
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const instance = new OrgChart<Row>()
      .container(container)
      .data(rows.data.map((row) => ({ ...row })))
      .nodeWidth(() => NODE_WIDTH)
      .nodeHeight(() => NODE_HEIGHT)
      .childrenMargin(() => 56)
      .siblingsMargin(() => 20)
      .neighbourMargin(() => 40)
      .compact(false)   // en 3.1.1 «Ajustar» no cuenta el modo compacto
      .initialExpandLevel(2)
      .svgHeight(container.clientHeight)
      .scaleExtent([0.2, 2])
      .duration(0)      // primera vista sin animación
      .nodeContent((node) => nodeHtml(node.data))
      .buttonContent(({ node }) => `<div class="ws-org-toggle">${node.data.reports || ''}</div>`)
      .nodeUpdate(function (node) {
        const highlighted = node.data._highlighted || node.data._upToTheRootHighlighted
        this.querySelector('.node-rect')?.setAttribute('stroke', highlighted ? BRAND : 'none')
        this.querySelector('.node-rect')?.setAttribute('stroke-width', highlighted ? '4' : '0')
      })
      .linkUpdate(function (node) {
        this.setAttribute('stroke', node.data._upToTheRootHighlighted ? BRAND : '#cbd5e1')
        this.setAttribute('stroke-width', node.data._upToTheRootHighlighted ? '3' : '1.5')
      })
      .render()

    // Primera vista (después de que la librería termine de dibujar): legible y desde arriba.
    const firstView = window.setTimeout(() => {
      showReadable(instance, container.clientWidth, container.clientHeight)
      instance.duration(reduceMotion ? 0 : 250)
    }, 0)
    chartRef.current = instance

    // Nombre → perfil sin recargar la página (navegación de React Router).
    const onClick = (event: MouseEvent) => {
      const link = (event.target as HTMLElement).closest<HTMLAnchorElement>('a[data-profile]')
      if (!link) return
      event.preventDefault()
      navigate(link.getAttribute('href')!)
    }
    container.addEventListener('click', onClick)
    return () => {
      window.clearTimeout(firstView)
      container.removeEventListener('click', onClick)
      container.replaceChildren()
      chartRef.current = null
    }
  }, [rows.data, navigate])

  function focusPerson(name: string) {
    const person = people.find((row) => row.name.toLowerCase() === name.trim().toLowerCase())
    if (!person || !chartRef.current) return
    chartRef.current.clearHighlighting().setUpToTheRootHighlighted(person.id).setCentered(person.id).render()
  }

  if (chart.isPending || (chart.isSuccess && rows.isPending)) {
    return <Skeleton className="h-[min(70dvh,44rem)] min-h-96 w-full rounded-2xl" aria-label="Cargando organigrama" />
  }
  if (chart.isError || rows.isError) {
    return (
      <Card>
        <EmptyState icon={Network} title="No se pudo cargar el organigrama" action={<Button variant="outline" onClick={() => void chart.refetch()}>Reintentar</Button>} />
      </Card>
    )
  }
  if (people.length === 0) {
    return (
      <Card>
        <EmptyState icon={Network} title="El organigrama está vacío" description="Aparecerá cuando Recursos Humanos registre el jefe directo de cada persona." />
      </Card>
    )
  }

  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 p-3">
        <label className="relative min-w-48 flex-1">
          <span className="sr-only">Buscar en el organigrama</span>
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" aria-hidden />
          <input
            list="org-people"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              focusPerson(event.target.value)
            }}
            placeholder="Buscar persona"
            className="h-10 w-full rounded-xl border border-slate-200 pr-3 pl-9 text-base focus:border-brand-500 focus:ring-4 focus:ring-brand-500/15 focus:outline-none sm:text-sm"
          />
          <datalist id="org-people">
            {people.map((row) => <option key={row.id} value={row.name} />)}
          </datalist>
        </label>
        <div className="flex items-center gap-1">
          <ChartButton label="Ajustar" onClick={() => chartRef.current?.fit()}><Maximize2 className="size-4" /></ChartButton>
          <ChartButton label="Abrir todo" onClick={() => chartRef.current?.expandAll().fit()}><ChevronsUpDown className="size-4" /></ChartButton>
          <ChartButton label="Cerrar" onClick={() => chartRef.current?.collapseAll().fit()}><ChevronsDownUp className="size-4" /></ChartButton>
          <ChartButton label="Acercar" iconOnly onClick={() => chartRef.current?.zoomIn()}><ZoomIn className="size-4" /></ChartButton>
          <ChartButton label="Alejar" iconOnly onClick={() => chartRef.current?.zoomOut()}><ZoomOut className="size-4" /></ChartButton>
        </div>
      </div>
      {chart.data.unassigned_count > 0 && (
        <p className="border-b border-slate-100 bg-slate-50 px-4 py-2 text-xs text-slate-500">
          {chart.data.unassigned_count === 1 ? '1 persona aún no tiene' : `${chart.data.unassigned_count} personas aún no tienen`} jefe directo registrado y no aparecen aquí.
        </p>
      )}
      <div ref={containerRef} className="ws-org-chart h-[min(70dvh,44rem)] min-h-96 w-full cursor-grab bg-canvas active:cursor-grabbing" />
    </Card>
  )
}

/** En teléfono los controles muestran solo el ícono (con su nombre para lectores de pantalla). */
function ChartButton({ label, iconOnly = false, children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; iconOnly?: boolean; children: ReactNode }) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      className={cn('pressable flex h-10 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-slate-600 transition-colors duration-150 hover:bg-slate-100', iconOnly && 'px-2.5')}
      {...props}
    >
      {children}
      {!iconOnly && <span className="hidden md:inline">{label}</span>}
    </button>
  )
}

/**
 * Si todo el árbol visible cabe a 70 % o más (sin pasar de 100 %), se centra completo; si no, se muestra
 * a 70 % con la raíz arriba al centro (se recorre arrastrando o con «Ajustar»).
 */
function showReadable(chart: OrgChart<Row>, width: number, height: number) {
  const { root, svg, zoomBehavior, centerG } = chart.getChartState()
  centerG.attr('transform', 'translate(0,0)')   // igual que «Ajustar»: las posiciones quedan en el plano real
  const nodes = root.descendants()
  // En 3.1.1 cada tarjeta se dibuja desde `x` hacia la derecha (no centrada en `x`): su centro es x + ancho/2.
  const x0 = Math.min(...nodes.map((node) => node.x)) - 40
  const x1 = Math.max(...nodes.map((node) => node.x)) + NODE_WIDTH + 40
  const y0 = Math.min(...nodes.map((node) => node.y)) - 32
  const y1 = Math.max(...nodes.map((node) => node.y)) + NODE_HEIGHT + 32
  const fitScale = Math.min(1, width / (x1 - x0), height / (y1 - y0))
  const transform = fitScale >= MIN_READABLE_SCALE
    ? zoomIdentity.translate(width / 2, height / 2).scale(fitScale).translate(-(x0 + x1) / 2, -(y0 + y1) / 2)
    : zoomIdentity.translate(width / 2, 24).scale(MIN_READABLE_SCALE).translate(-(root.x + NODE_WIDTH / 2), -root.y)
  svg.call(zoomBehavior.transform, transform)
}

function companyRow(): Row {
  return { id: ROOT_ID, parentId: null, personId: null, name: env.projectName, initials: '', jobTitle: 'Organigrama', department: '', reports: 0, photo: null }
}

function flatten(nodes: ChartNode[], parentId: string = ROOT_ID, out: Row[] = []): Row[] {
  for (const node of nodes) {
    out.push({
      id: String(node.id), parentId, personId: node.id, name: node.name, initials: node.initials,
      jobTitle: node.job_title, department: node.department?.name ?? '', reports: node.reports_count, photo: node.avatar_url || null,
    })
    flatten(node.children, String(node.id), out)
  }
  return out
}

const escapeHtml = (text: string) => text.replace(/[&<>"']/g, (char) => `&#${char.charCodeAt(0)};`)

/** HTML de cada tarjeta (d3-org-chart dibuja HTML dentro del SVG). Todo el texto va escapado. */
function nodeHtml(row: Row) {
  if (row.personId === null) {
    return `<div class="ws-org-card ws-org-card--root"><img src="/icons/favicon-32.png" alt="" class="ws-org-logo" /><div><p class="ws-org-name">${escapeHtml(row.name)}</p><p class="ws-org-job">${escapeHtml(row.jobTitle)}</p></div></div>`
  }
  const photo = row.photo
    ? `<img src="${row.photo}" alt="" class="ws-org-photo" />`
    : `<span class="ws-org-photo ws-org-initials">${escapeHtml(row.initials)}</span>`
  return `<div class="ws-org-card">${photo}<div class="ws-org-text">
    <a href="/profile/${row.personId}" data-profile class="ws-org-name">${escapeHtml(row.name)}</a>
    ${row.jobTitle ? `<p class="ws-org-job">${escapeHtml(row.jobTitle)}</p>` : ''}
    ${row.department ? `<span class="ws-org-dept">${escapeHtml(row.department)}</span>` : ''}
  </div></div>`
}
