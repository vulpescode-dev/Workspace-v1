import Placeholder from '@tiptap/extension-placeholder'
import { EditorContent, useEditor, useEditorState, type Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import {
  Bold, Heading2, Heading3, Italic, Link2, List, ListOrdered, Minus, Quote, Redo2, Strikethrough, Underline, Undo2,
  type LucideIcon,
} from 'lucide-react'

import { cn } from '@/lib/cn'

/**
 * Editor del contenido (Tiptap). Solo produce lo que el servidor deja pasar (títulos H2/H3, listas,
 * enlaces, citas, separador); el HTML se limpia otra vez al guardar. Se ve con los mismos estilos que
 * la noticia publicada (`.ws-article`).
 */
export function RichTextEditor({ value, onChange, label }: { value: string; onChange: (html: string) => void; label: string }) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [2, 3] },
        code: false,
        codeBlock: false,
        link: { openOnClick: false, autolink: true, defaultProtocol: 'https', HTMLAttributes: { target: '_blank' } },
      }),
      Placeholder.configure({ placeholder: 'Escribe la noticia… Usa los títulos para dividirla en secciones.' }),
    ],
    content: value,
    editorProps: { attributes: { class: 'ws-article min-h-80 px-4 py-4 outline-none sm:px-6', 'aria-label': label, 'aria-multiline': 'true', role: 'textbox' } },
    onUpdate: ({ editor: current }) => onChange(current.isEmpty ? '' : current.getHTML()),
  })

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-surface focus-within:border-brand-500 focus-within:ring-4 focus-within:ring-brand-500/15">
      <Toolbar editor={editor} />
      <EditorContent editor={editor} />
    </div>
  )
}

function Toolbar({ editor }: { editor: Editor }) {
  // Solo se vuelve a pintar la barra cuando cambia algo que muestra (no en cada tecla).
  const state = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      bold: e.isActive('bold'), italic: e.isActive('italic'), underline: e.isActive('underline'), strike: e.isActive('strike'),
      h2: e.isActive('heading', { level: 2 }), h3: e.isActive('heading', { level: 3 }),
      bullet: e.isActive('bulletList'), ordered: e.isActive('orderedList'), quote: e.isActive('blockquote'), link: e.isActive('link'),
      canUndo: e.can().undo(), canRedo: e.can().redo(),
    }),
  })
  const chain = () => editor.chain().focus()

  function toggleLink() {
    if (state.link) return chain().unsetLink().run()
    const url = window.prompt('Dirección del enlace (https://…)')?.trim()
    if (!url) return
    chain().extendMarkRange('link').setLink({ href: /^(https?:|mailto:)/i.test(url) ? url : `https://${url}` }).run()
  }

  const groups: { icon: LucideIcon; label: string; active?: boolean; disabled?: boolean; run: () => void }[][] = [
    [
      { icon: Heading2, label: 'Título', active: state.h2, run: () => chain().toggleHeading({ level: 2 }).run() },
      { icon: Heading3, label: 'Subtítulo', active: state.h3, run: () => chain().toggleHeading({ level: 3 }).run() },
    ],
    [
      { icon: Bold, label: 'Negritas', active: state.bold, run: () => chain().toggleBold().run() },
      { icon: Italic, label: 'Cursiva', active: state.italic, run: () => chain().toggleItalic().run() },
      { icon: Underline, label: 'Subrayado', active: state.underline, run: () => chain().toggleUnderline().run() },
      { icon: Strikethrough, label: 'Tachado', active: state.strike, run: () => chain().toggleStrike().run() },
      { icon: Link2, label: state.link ? 'Quitar enlace' : 'Enlace', active: state.link, run: toggleLink },
    ],
    [
      { icon: List, label: 'Lista con viñetas', active: state.bullet, run: () => chain().toggleBulletList().run() },
      { icon: ListOrdered, label: 'Lista numerada', active: state.ordered, run: () => chain().toggleOrderedList().run() },
      { icon: Quote, label: 'Cita', active: state.quote, run: () => chain().toggleBlockquote().run() },
      { icon: Minus, label: 'Separador', run: () => chain().setHorizontalRule().run() },
    ],
    [
      { icon: Undo2, label: 'Deshacer', disabled: !state.canUndo, run: () => chain().undo().run() },
      { icon: Redo2, label: 'Rehacer', disabled: !state.canRedo, run: () => chain().redo().run() },
    ],
  ]

  return (
    <div role="toolbar" aria-label="Formato" className="sticky top-0 z-10 flex flex-wrap items-center gap-1 border-b border-slate-100 bg-surface/95 px-2 py-1.5 backdrop-blur">
      {groups.map((group, index) => (
        <div key={index} className={cn('flex items-center gap-0.5', index > 0 && 'border-l border-slate-100 pl-1')}>
          {group.map(({ icon: Icon, label, active, disabled, run }) => (
            <button
              key={label}
              type="button"
              title={label}
              aria-label={label}
              aria-pressed={active}
              disabled={disabled}
              onMouseDown={(event) => event.preventDefault()}
              onClick={run}
              className={cn(
                'pressable grid size-9 place-items-center rounded-lg transition-colors duration-150 disabled:opacity-35',
                active ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100',
              )}
            >
              <Icon className="size-[18px]" aria-hidden />
            </button>
          ))}
        </div>
      ))}
    </div>
  )
}
