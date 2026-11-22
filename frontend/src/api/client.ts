// Llamadas a la API de Fake Music Hunter.

import type {
  AnalysisResult, Health, Job, LibraryFolder, LibraryJobParams, Page, ResultFilters,
} from "./types";

/** Error de la API con el mensaje que devuelve el servidor (campo "detail"). */
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

// Sin límite, una petición a un servidor que no contesta puede quedarse
// colgada minutos, y mientras tanto no se reintenta ni se avisa al usuario.
const DEFAULT_TIMEOUT_MS = 15_000;
const HEALTH_TIMEOUT_MS = 5_000;

async function request<T>(path: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { ...init, signal: AbortSignal.timeout(timeoutMs) });
  } catch {
    throw new ApiError(0, "No se puede conectar con el servidor");
  }
  if (!response.ok) {
    throw new ApiError(response.status, await readErrorMessage(response));
  }
  return response.json() as Promise<T>;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
  } catch {
    // La respuesta no era JSON; usamos el mensaje genérico
  }
  return `Error del servidor (${response.status})`;
}

type QueryValue = string | number | undefined | (string | number)[];

/** Añade los parámetros a la ruta. Las listas se envían repitiendo el parámetro. */
function withQuery(path: string, params: Record<string, QueryValue>): string {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    const values = Array.isArray(value) ? value : [value];
    for (const item of values) {
      if (item !== undefined && item !== "") query.append(key, String(item));
    }
  }
  const text = query.toString();
  return text ? `${path}?${text}` : path;
}

export const api = {
  health: () => request<Health>("/api/health", undefined, HEALTH_TIMEOUT_MS),

  library: (path: string) => request<LibraryFolder>(withQuery("/api/library", { path })),

  createLibraryJob: (params: LibraryJobParams) =>
    request<Job>("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    }),

  jobs: (offset = 0, limit = 50) => request<Page<Job>>(withQuery("/api/jobs", { offset, limit })),

  job: (id: string) => request<Job>(`/api/jobs/${id}`),

  results: (id: string, filters: ResultFilters) =>
    request<Page<AnalysisResult>>(withQuery(`/api/jobs/${id}/results`, { ...filters })),

  cancelJob: (id: string) => request<Job>(`/api/jobs/${id}/cancel`, { method: "POST" }),

  eventsUrl: (id: string) => `/api/jobs/${id}/events`,

  reportUrl: (id: string, format: "csv" | "json") => `/api/jobs/${id}/report.${format}`,
};

/**
 * Sube archivos y crea un trabajo con ellos.
 *
 * Usa XMLHttpRequest en lugar de fetch porque fetch no informa del
 * progreso de la subida.
 */
export function uploadFiles(files: File[], onProgress: (fraction: number) => void): Promise<Job> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    files.forEach((file) => form.append("files", file, file.name));

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/jobs/upload");
    xhr.responseType = "json";

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.response as Job);
      } else {
        const detail = xhr.response?.detail;
        reject(new ApiError(xhr.status, typeof detail === "string" ? detail : `Error del servidor (${xhr.status})`));
      }
    };
    xhr.onerror = () => reject(new ApiError(0, "No se puede conectar con el servidor"));

    xhr.send(form);
  });
}
