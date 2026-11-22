import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { uploadFiles } from "../api/client";
import { formatBytes } from "../format";
import { useHealth } from "../hooks/useHealth";
import { Icon } from "./Icon";

const ALLOWED_EXTENSIONS = [".mp3", ".flac", ".wav"];

interface SelectedFile {
  file: File;
  problem: string | null;   // motivo por el que no se puede subir, si lo hay
}

/** Selección (o arrastre) de archivos, validación y subida con progreso. */
export function UploadPanel() {
  const health = useHealth();
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const [selected, setSelected] = useState<SelectedFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const maxMb = health.data?.max_upload_mb ?? 500;

  const addFiles = (files: FileList | null) => {
    if (!files) return;
    const added = Array.from(files).map((file) => ({ file, problem: validate(file, maxMb) }));
    setSelected((current) => [...current, ...added]);
    setError(null);
  };

  const validFiles = selected.filter((item) => item.problem === null).map((item) => item.file);
  const uploading = progress !== null;

  const startUpload = async () => {
    setError(null);
    setProgress(0);
    try {
      const job = await uploadFiles(validFiles, setProgress);
      navigate(`/jobs/${job.id}`);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "No se pudo subir");
      setProgress(null);
    }
  };

  return (
    <div className="card">
      <div
        className={`dropzone ${dragging ? "dragging" : ""}`}
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") inputRef.current?.click(); }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
      >
        <p><strong>Arrastra aquí tus archivos</strong> o haz clic para elegirlos</p>
        <p className="small muted">MP3, FLAC o WAV · máximo {maxMb} MB por archivo</p>
        <input ref={inputRef} type="file" multiple accept={ALLOWED_EXTENSIONS.join(",")} hidden
          onChange={(e) => { addFiles(e.target.files); e.target.value = ""; }} />
      </div>

      {selected.length > 0 && (
        <ul className="file-list">
          {selected.map((item, index) => (
            <li key={`${item.file.name}-${index}`} className={item.problem ? "file-invalid" : ""}>
              <span>{item.file.name} <span className="muted small">({formatBytes(item.file.size)})</span></span>
              <span className="small">
                {item.problem ?? ""}
                {!uploading && (
                  <button className="link-button" style={{ marginLeft: 8 }} aria-label={`Quitar ${item.file.name}`}
                    onClick={() => setSelected((current) => current.filter((_, i) => i !== index))}>
                    <Icon name="x" /> Quitar
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      )}

      {error && <div className="notice notice-error">{error}</div>}

      {uploading ? (
        <div>
          <p className="small">Subiendo… {Math.round((progress ?? 0) * 100)} %</p>
          <div className="progress" role="progressbar" aria-label="Progreso de la subida"
            aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round((progress ?? 0) * 100)}>
            <div className="progress-bar" style={{ width: `${(progress ?? 0) * 100}%` }} />
          </div>
        </div>
      ) : (
        <div className="row" style={{ marginTop: 12 }}>
          <button className="button-primary" disabled={validFiles.length === 0} onClick={startUpload}>
            Analizar {validFiles.length} {validFiles.length === 1 ? "archivo" : "archivos"}
          </button>
          {selected.length > 0 && <button onClick={() => setSelected([])}>Vaciar lista</button>}
        </div>
      )}
    </div>
  );
}

function validate(file: File, maxMb: number): string | null {
  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    return "Formato no soportado (solo MP3, FLAC o WAV)";
  }
  if (file.size > maxMb * 1024 * 1024) {
    return `Supera el máximo de ${maxMb} MB`;
  }
  return null;
}
