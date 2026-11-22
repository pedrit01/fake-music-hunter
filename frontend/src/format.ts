// Textos y formatos que se muestran al usuario.

import type { Classification, Job, JobStatus } from "./api/types";

export const CLASSIFICATION_LABELS: Record<Classification, string> = {
  legitimate: "Legítimo",
  fake: "Fake",
  suspicious: "Sospechoso",
  error: "Error",
};

export const STATUS_LABELS: Record<JobStatus, string> = {
  queued: "En cola",
  running: "Analizando",
  completed: "Completado",
  failed: "Fallido",
  cancelled: "Cancelado",
};

const dateFormatter = new Intl.DateTimeFormat("es-ES", { dateStyle: "medium", timeStyle: "short" });

export function formatDate(iso: string | null): string {
  return iso ? dateFormatter.format(new Date(iso)) : "—";
}

export function formatPercent(part: number, total: number): string {
  const percent = total > 0 ? (part / total) * 100 : 0;
  return `${percent.toLocaleString("es-ES", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`;
}

export function formatNumber(value: number | null, unit: string, decimals = 1): string {
  return value === null ? "—" : `${value.toLocaleString("es-ES", { maximumFractionDigits: decimals })} ${unit}`;
}

export function formatBitrate(bps: number | null): string {
  return bps === null ? "—" : `${Math.round(bps / 1000)} kbps`;
}

export function formatBytes(bytes: number | null): string {
  if (bytes === null) return "—";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toLocaleString("es-ES", { maximumFractionDigits: 1 })} ${units[unit]}`;
}

/** Describe de dónde salen los archivos de un trabajo. */
export function describeSource(job: Job): string {
  if (job.source === "upload") {
    const count = job.params.files?.length ?? 0;
    return `Subida de ${count} ${count === 1 ? "archivo" : "archivos"}`;
  }
  const path = job.params.path ? job.params.path : "Biblioteca completa";
  return `Carpeta: ${path}`;
}
