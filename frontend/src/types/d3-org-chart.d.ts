/** Tipos mínimos de d3-org-chart 3.1.1 (la librería no trae los suyos): solo lo que usa el organigrama. */
declare module 'd3-org-chart' {
  export interface OrgChartNode<T> {
    data: T & { _highlighted?: boolean; _upToTheRootHighlighted?: boolean; _expanded?: boolean }
    depth: number
    /** Posición en el plano del organigrama (layout «top»: x = centro, y = borde superior). */
    x: number
    y: number
    children?: OrgChartNode<T>[]
    descendants(): OrgChartNode<T>[]
  }

  export class OrgChart<T = Record<string, unknown>> {
    container(element: HTMLElement): this
    data(rows: T[]): this
    nodeId(accessor: (row: T) => string): this
    parentNodeId(accessor: (row: T) => string | null): this
    nodeWidth(accessor: () => number): this
    nodeHeight(accessor: () => number): this
    childrenMargin(accessor: () => number): this
    siblingsMargin(accessor: () => number): this
    neighbourMargin(accessor: () => number): this
    compact(enabled: boolean): this
    duration(ms: number): this
    initialExpandLevel(level: number): this
    svgHeight(height: number): this
    scaleExtent(extent: [number, number]): this
    nodeContent(render: (node: OrgChartNode<T>) => string): this
    buttonContent(render: (args: { node: OrgChartNode<T> }) => string): this
    nodeUpdate(update: (this: SVGGElement, node: OrgChartNode<T>) => void): this
    linkUpdate(update: (this: SVGPathElement, node: OrgChartNode<T>) => void): this
    render(): this
    fit(options?: { animate?: boolean }): this
    expandAll(): this
    collapseAll(): this
    zoomIn(): void
    zoomOut(): void
    setCentered(id: string): this
    setUpToTheRootHighlighted(id: string): this
    clearHighlighting(): this
    getChartState(): {
      root: OrgChartNode<T>
      /** Grupo que la librería mueve para centrar la raíz en el primer dibujo («Ajustar» lo regresa a 0,0). */
      centerG: { attr: (name: string, value: string) => unknown }
      svg: { call: (behavior: unknown, ...args: unknown[]) => void }
      zoomBehavior: { transform: unknown }
    }
  }
}
