import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import type { Classification, Job } from "../api/types";
import { StatusBadge } from "../components/Badges";
import { ResultsTable } from "../components/ResultsTable";
import { Summary } from "../components/Summary";
import { describeSource, formatDate, STATUS_LABELS } from "../format";
import { useDocumentTitle } from "../hooks/useDocumentTitle";
import { isActive, useLiveJob } from "../hooks/useLiveJob";

/**
 * Título de la pestaña según el estado del trabajo. El porcentaje se redondea
 * hacia abajo a entero, para que no cambie con cada archivo.
 */
function jobTitle(job: Job | undefined): string {
  if (!job) return "Análisis";
  if (job.status === "running") {
    // Con todos los archivos procesados el trabajo aún tarda un instante en cerrarse:
    // nos quedamos en 99 % para no mostrar "100 % · Analizando…"
    const percent = job.total > 0 ? Math.min(99, Math.floor((job.processed / job.total) * 100)) : 0;
    return `${percent} % · Analizando…`;
  }
  return STATUS_LABELS[job.status];
}

export function JobPage() {
  const { jobId = "" } = useParams();
  const job = useLiveJob(jobId);
  const queryClient = useQueryClient();
  const [classification, setClassification] = useState<Classification[]>([]);
  useDocumentTitle(jobTitle(job.data));

  const cancel = useMutation({
    mutationFn: () => api.cancelJob(jobId),
    onSuccess: (updated) => queryClient.setQueryData(["job", jobId], updated),
  });

  if (job.isPending) return <p className="muted">Cargando análisis…</p>;
  if (job.isError && !job.data) {
    return (
      <div className="notice notice-error">
        {job.error.message}. <Link to="/jobs">Volver al historial</Link>
      </div>
    );
  }

  const data = job.data;
  const active = isActive(data);
  const fraction = data.total > 0 ? data.processed / data.total : 0;

  return (
    <>
      <div className="row" style={{ marginBottom: 8 }}>
        <h1 style={{ margin: 0 }}>{describeSource(data)}</h1>
        <StatusBadge value={data.status} />
      </div>
      <p className="muted small">
        Creado: {formatDate(data.created_at)}
        {data.finished_at && <> · Terminado: {formatDate(data.finished_at)}</>}
      </p>

      {data.status === "failed" && data.error && <div className="notice notice-error">{data.error}</div>}
      {cancel.isError && <div className="notice notice-error">{cancel.error.message}</div>}

      <div className="card">
        <div className="row" style={{ marginBottom: 8 }}>
          <strong aria-live="polite">
            {data.status === "queued" ? "Preparando la lista de archivos…" : `${data.processed} de ${data.total} archivos analizados`}
          </strong>
          <span className="spacer" />
          {active && (
            <button className="button-danger" disabled={cancel.isPending} onClick={() => cancel.mutate()}>
              {cancel.isPending ? "Cancelando…" : "Cancelar"}
            </button>
          )}
          <a className="button" href={api.reportUrl(jobId, "csv")} download>Descargar CSV</a>
          <a className="button" href={api.reportUrl(jobId, "json")} download>Descargar JSON</a>
        </div>
        <div className="progress" role="progressbar" aria-label="Progreso del análisis" aria-valuemin={0} aria-valuemax={data.total} aria-valuenow={data.processed}>
          <div className="progress-bar" style={{ width: `${fraction * 100}%` }} />
        </div>
      </div>

      <div className="card">
        <Summary counts={data.counts} total={data.processed} selected={classification} onSelect={setClassification} />
      </div>

      <ResultsTable jobId={jobId} classification={classification} onClassificationChange={setClassification} />
    </>
  );
}
