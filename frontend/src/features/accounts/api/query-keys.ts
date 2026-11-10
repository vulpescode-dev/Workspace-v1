/** Llaves de caché de esta feature: invalidar `accountsKeys.all` refresca todo lo de cuentas. */
export const accountsKeys = {
  all: ['accounts'] as const,
  me: () => [...accountsKeys.all, 'me'] as const,
  birthdays: () => [...accountsKeys.all, 'birthdays'] as const,
}
