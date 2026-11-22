import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { api } from "../api/client";
import { ACTIVE_STATUSES, type Job } from "../api/types";

// Como mucho recargamos la tabla de resultados una vez por segundo,
// aunque lleguen muchos avisos de progreso seguidos.
const RESULTS_REFRESH_MS = 1000;
// Si el SSE no funciona, consultamos el estado con esta frecuencia.
const POLL_INTERVAL_MS = 2000;

export function isActive(job: Job | undefined): boolean {
  return job !== undefined && ACTIVE_STATUSES.includes(job.status);
}

/**
 * Estado de un trabajo, actualizado en vivo.
 *
 * Mientras el trabajo está activo escucha los eventos SSE del servidor. Si la
 * conexión SSE falla, pasa a consultar el estado cada pocos segundos.
 */
export function useLiveJob(jobId: string) {
  const queryClient = useQueryClient();
  const [sseFailed, setSseFailed] = useState(false);
  const refreshTimer = useRef<number | null>(null);

  const job = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api.job(jobId),
    refetchInterval: (query) => (isActive(query.state.data) && sseFailed ? POLL_INTERVAL_MS : false),
  });

  const active = isActive(job.data);

  useEffect(() => {
    if (!active || sseFailed) return;

    const refreshResults = (immediately: boolean) => {
      if (immediately) {
        void queryClient.invalidateQueries({ queryKey: ["results", jobId] });
        return;
      }
      if (refreshTimer.current !== null) return;
      refreshTimer.current = window.setTimeout(() => {
        refreshTimer.current = null;
        void queryClient.invalidateQueries({ queryKey: ["results", jobId] });
      }, RESULTS_REFRESH_MS);
    };

    const source = new EventSource(api.eventsUrl(jobId));
    const handle = (event: MessageEvent, finished: boolean) => {
      const data = JSON.parse(event.data) as { job: Job };
      queryClient.setQueryData(["job", jobId], data.job);
      refreshResults(finished);
      if (finished) {
        source.close();
        void queryClient.invalidateQueries({ queryKey: ["jobs"] });
      }
    };

    source.addEventListener("progress", (event) => handle(event, false));
    source.addEventListener("done", (event) => handle(event, true));
    source.onerror = () => {
      source.close();
      setSseFailed(true);
    };

    return () => {
      source.close();
      if (refreshTimer.current !== null) {
        window.clearTimeout(refreshTimer.current);
        refreshTimer.current = null;
      }
    };
  }, [jobId, active, sseFailed, queryClient]);

  // Con polling, refrescamos los resultados cada vez que cambia el progreso
  const processed = job.data?.processed;
  useEffect(() => {
    if (sseFailed) void queryClient.invalidateQueries({ queryKey: ["results", jobId] });
  }, [processed, sseFailed, jobId, queryClient]);

  return job;
}
