import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api/client";
import { useHealth } from "../hooks/useHealth";

const FORMATS = [".flac", ".wav", ".mp3"];

/** Navegador de carpetas de la biblioteca montada y lanzamiento del análisis. */
export function LibraryBrowser() {
  const health = useHealth();
  const [path, setPath] = useState("");
  const [recursive, setRecursive] = useState(true);
  const [formats, setFormats] = useState<string[]>(FORMATS);
  const navigate = useNavigate();

  const libraryAvailable = health.data?.library_available ?? false;
  const folder = useQuery({
    queryKey: ["library", path],
    queryFn: () => api.library(path),
    enabled: libraryAvailable,
  });

  const startJob = useMutation({
    mutationFn: () => api.createLibraryJob({ path, recursive, formats }),
    onSuccess: (job) => navigate(`/jobs/${job.id}`),
  });

  if (health.data && !libraryAvailable) {
    return (
      <div className="notice notice-info">
        <strong>No hay ninguna biblioteca de música montada.</strong>
        <p className="small">
          Monta tu carpeta de música en el contenedor (por ejemplo <code>-v /ruta/musica:/music:ro</code>)
          para poder analizarla desde aquí. Mientras tanto, puedes usar la pestaña "Subir archivos".
        </p>
      </div>
    );
  }

  const toggleFormat = (format: string) =>
    setFormats((current) =>
      current.includes(format) ? current.filter((f) => f !== format) : [...current, format]);

  const audioCounts = folder.data?.audio_files ?? {};
  const filesHere = FORMATS.reduce((sum, format) => sum + (audioCounts[format] ?? 0), 0);

  return (
    <div className="card">
      <Breadcrumbs path={path} onNavigate={setPath} />

      {folder.isError && <div className="notice notice-error">{folder.error.message}</div>}
      {folder.isPending && <p className="muted">Cargando carpeta…</p>}

      {folder.data && (
        <>
          <ul className="folder-list" aria-label="Subcarpetas">
            {folder.data.parent !== null && (
              <li><button onClick={() => setPath(folder.data.parent ?? "")}>⬆️ Subir un nivel</button></li>
            )}
            {folder.data.directories.map((directory) => (
              <li key={directory.path}>
                <button onClick={() => setPath(directory.path)}>📁 {directory.name}</button>
              </li>
            ))}
            {folder.data.directories.length === 0 && (
              <li className="muted" style={{ padding: "10px 14px" }}>No hay subcarpetas</li>
            )}
          </ul>
          <p className="small muted">
            En esta carpeta: {filesHere} archivos de audio
            ({FORMATS.map((format) => `${audioCounts[format] ?? 0} ${format.slice(1).toUpperCase()}`).join(", ")})
          </p>
        </>
      )}

      <div className="row" style={{ marginBottom: 16 }}>
        <label className="check">
          <input type="checkbox" checked={recursive} onChange={(e) => setRecursive(e.target.checked)} />
          Incluir subcarpetas
        </label>
        <fieldset className="check-group">
          <legend>Formatos</legend>
          {FORMATS.map((format) => (
            <label key={format} className="check">
              <input type="checkbox" checked={formats.includes(format)} onChange={() => toggleFormat(format)} />
              {format.slice(1).toUpperCase()}
            </label>
          ))}
        </fieldset>
      </div>

      {startJob.isError && <div className="notice notice-error">{startJob.error.message}</div>}
      <button className="button-primary" disabled={formats.length === 0 || startJob.isPending || !folder.data}
        onClick={() => startJob.mutate()}>
        {startJob.isPending ? "Creando análisis…" : `Analizar ${path ? `"${path}"` : "toda la biblioteca"}`}
      </button>
    </div>
  );
}

function Breadcrumbs({ path, onNavigate }: { path: string; onNavigate: (path: string) => void }) {
  const parts = path ? path.split("/") : [];

  return (
    <nav className="breadcrumbs" aria-label="Ruta">
      <button className="link-button" onClick={() => onNavigate("")}>Biblioteca</button>
      {parts.map((part, index) => {
        const partPath = parts.slice(0, index + 1).join("/");
        const isLast = index === parts.length - 1;
        return (
          <span key={partPath}>
            <span className="muted"> / </span>
            {isLast ? <strong>{part}</strong>
              : <button className="link-button" onClick={() => onNavigate(partPath)}>{part}</button>}
          </span>
        );
      })}
    </nav>
  );
}
