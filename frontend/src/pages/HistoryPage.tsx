import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { ACTIVE_STATUSES, CLASSIFICATIONS } from "../api/types";
import { ClassificationBadge, StatusBadge } from "../components/Badges";
import { describeSource, formatDate } from "../format";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

const PAGE_SIZE = 25;

export function HistoryPage() {
  const [offset, setOffset] = useState(0);
  useDocumentTitle("Historial");
  const jobs = useQuery({
    queryKey: ["jobs", offset],
    queryFn: () => api.jobs(offset, PAGE_SIZE),
    // Mientras haya trabajos en marcha, refrescamos su progreso
    refetchInterval: (query) =>
      query.state.data?.items.some((job) => ACTIVE_STATUSES.includes(job.status)) ? 3000 : false,
  });

  const total = jobs.data?.total ?? 0;

  return (
    <>
      <h1>Historial</h1>
      {jobs.isError && !jobs.data && <div className="notice notice-error">{jobs.error.message}</div>}
      {jobs.isPending && <p className="muted">Cargando…</p>}
      {jobs.data && jobs.data.items.length === 0 && (
        <div className="notice notice-info">
          Todavía no hay análisis. <Link to="/">Lanza el primero</Link>.
        </div>
      )}

      {jobs.data && jobs.data.items.length > 0 && (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Análisis</th>
                <th>Estado</th>
                <th className="hide-mobile">Fecha</th>
                <th className="hide-mobile">Resumen</th>
              </tr>
            </thead>
            <tbody>
              {jobs.data.items.map((job) => (
                <tr key={job.id}>
                  <td>
                    <Link to={`/jobs/${job.id}`}>{describeSource(job)}</Link>
                    <div className="small muted">{job.processed} de {job.total} archivos</div>
                  </td>
                  <td><StatusBadge value={job.status} /></td>
                  <td className="hide-mobile small">{formatDate(job.created_at)}</td>
                  <td className="hide-mobile">
                    <div className="row" style={{ gap: 6 }}>
                      {CLASSIFICATIONS.filter((c) => job.counts[c] > 0).map((c) => (
                        <span key={c}><ClassificationBadge value={c} /> {job.counts[c]}</span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {total > PAGE_SIZE && (
            <div className="pagination">
              <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Anterior</button>
              <span className="small muted">{offset + 1}–{Math.min(offset + PAGE_SIZE, total)} de {total}</span>
              <button disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>Siguiente</button>
            </div>
          )}
        </div>
      )}
    </>
  );
}
