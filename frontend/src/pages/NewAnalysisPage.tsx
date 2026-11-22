import { useState } from "react";

import { LibraryBrowser } from "../components/LibraryBrowser";
import { UploadPanel } from "../components/UploadPanel";
import { useDocumentTitle } from "../hooks/useDocumentTitle";

type Tab = "library" | "upload";

export function NewAnalysisPage() {
  const [tab, setTab] = useState<Tab>("library");
  useDocumentTitle("Nuevo análisis");

  return (
    <>
      <h1>Nuevo análisis</h1>
      <p className="muted">
        Detecta archivos FLAC, WAV o MP3 convertidos desde formatos de menor calidad.
      </p>
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "library"} className={tab === "library" ? "active" : ""}
          onClick={() => setTab("library")}>
          Biblioteca
        </button>
        <button role="tab" aria-selected={tab === "upload"} className={tab === "upload" ? "active" : ""}
          onClick={() => setTab("upload")}>
          Subir archivos
        </button>
      </div>
      {tab === "library" ? <LibraryBrowser /> : <UploadPanel />}
    </>
  );
}
