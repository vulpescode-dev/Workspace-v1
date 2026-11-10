/** Solo en desarrollo (`/dev/errors/500`): truena al dibujarse para ver la pantalla de error real. */
export function DevThrowErrorPage(): never {
  throw new Error('Error de prueba (/dev/errors/500)')
}
