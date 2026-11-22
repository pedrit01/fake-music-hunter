// Tipos de la API. Deben coincidir con los modelos de src/web/schemas.py
// y con AnalysisResult de src/core/result.py.

export type Classification = "legitimate" | "fake" | "suspicious" | "error";

export const CLASSIFICATIONS: Classification[] = ["legitimate", "fake", "suspicious", "error"];

export type JobStatus = "queued" | "running" | "completed" | "failed" | "cancelled";

export const ACTIVE_STATUSES: JobStatus[] = ["queued", "running"];

export interface Health {
  status: string;
  version: string;
  library_available: boolean;
  max_upload_mb: number;
}

export interface LibraryFolder {
  path: string;
  parent: string | null;
  directories: { name: string; path: string }[];
  audio_files: Record<string, number>;
}

export interface LibraryJobParams {
  path: string;
  recursive: boolean;
  formats: string[];
}

export interface UploadJobParams {
  files: string[];
}

export interface Job {
  id: string;
  source: "library" | "upload";
  params: Partial<LibraryJobParams & UploadJobParams>;
  status: JobStatus;
  total: number;
  processed: number;
  counts: Record<Classification, number>;
  error: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface AnalysisResult {
  file_name: string;
  file_path: string;
  format: string;
  classification: Classification;
  reason: string;
  bitrate: number | null;
  sample_rate: number | null;
  channels: number | null;
  duration: number | null;
  file_size: number | null;
  cutoff_frequency: number | null;
  spectral_presence: number | null;
  high_freq_energy: number | null;
  has_content_above_20k: boolean | null;
  dynamic_range: number | null;
}

export interface ResultFilters {
  classification?: Classification;
  format?: string;
  q?: string;
  offset?: number;
  limit?: number;
}
