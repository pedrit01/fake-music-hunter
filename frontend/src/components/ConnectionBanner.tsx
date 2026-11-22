import { useHealth } from "../hooks/useHealth";

/** Aviso fijo arriba cuando el servidor deja de responder. */
export function ConnectionBanner() {
  const health = useHealth();

  if (!health.isError) return null;
  return (
    <div className="connection-banner" role="alert">
      Sin conexión con el servidor. Reintentando…
    </div>
  );
}
