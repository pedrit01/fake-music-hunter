/** Iconos SVG propios: se ven igual en todos los sistemas, a diferencia de los emojis. */
export type IconName = "music" | "folder" | "arrow-up" | "x";

// Trazos de 24 × 24 con línea de 2 px, al estilo de los iconos de interfaz habituales
const PATHS: Record<IconName, string> = {
  music: "M9 18V5l12-2v13M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0zm12-2a3 3 0 1 1-6 0 3 3 0 0 1 6 0z",
  folder: "M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  "arrow-up": "M12 19V5M5 12l7-7 7 7",
  x: "M18 6 6 18M6 6l12 12",
};

/**
 * Icono decorativo: mide 1em, toma el color del texto y se oculta a los
 * lectores de pantalla, porque el texto que lo acompaña ya da el significado.
 */
export function Icon({ name }: { name: IconName }) {
  return (
    <svg className="icon" viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor"
      strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d={PATHS[name]} />
    </svg>
  );
}
