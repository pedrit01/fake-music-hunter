import type { Classification, JobStatus } from "../api/types";
import { CLASSIFICATION_LABELS, STATUS_LABELS } from "../format";

export function ClassificationBadge({ value }: { value: Classification }) {
  return <span className={`badge badge-${value}`}>{CLASSIFICATION_LABELS[value]}</span>;
}

export function StatusBadge({ value }: { value: JobStatus }) {
  return <span className="badge badge-status">{STATUS_LABELS[value]}</span>;
}
