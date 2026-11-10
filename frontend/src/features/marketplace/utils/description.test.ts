import { describe, expect, it } from 'vitest'

import { toBlocks } from './description'

describe('toBlocks (descripción de un anuncio)', () => {
  it('líneas vacías separan párrafos y los saltos simples se conservan', () => {
    expect(toBlocks('Hola\nsegunda línea\n\nOtro párrafo')).toEqual([
      { kind: 'p', text: 'Hola\nsegunda línea' },
      { kind: 'p', text: 'Otro párrafo' },
    ])
  })

  it('reconoce viñetas con -, •, * y números', () => {
    expect(toBlocks('- uno\n• dos\n* tres\n1. cuatro\n2) cinco')).toEqual([
      { kind: 'ul', items: ['uno', 'dos', 'tres', 'cuatro', 'cinco'] },
    ])
  })

  it('una línea corta que termina en «:» es subtítulo; una larga no', () => {
    expect(toBlocks('Incluye:\n- Cable')).toEqual([
      { kind: 'h', text: 'Incluye' },
      { kind: 'ul', items: ['Cable'] },
    ])
    const long = 'Medidas: 45 cm de alto x 18 cm de base y pesa más o menos 1.2 kg:'
    expect(toBlocks(long)).toEqual([{ kind: 'p', text: long }])
  })

  it('un párrafo justo después de una lista abre un bloque nuevo', () => {
    expect(toBlocks('- a\n- b\nTexto')).toEqual([
      { kind: 'ul', items: ['a', 'b'] },
      { kind: 'p', text: 'Texto' },
    ])
  })

  it('acepta saltos de Windows (CRLF) y texto vacío', () => {
    expect(toBlocks('Uno\r\n\r\nDos')).toEqual([{ kind: 'p', text: 'Uno' }, { kind: 'p', text: 'Dos' }])
    expect(toBlocks('')).toEqual([])
    expect(toBlocks('   \n  ')).toEqual([])
  })
})
