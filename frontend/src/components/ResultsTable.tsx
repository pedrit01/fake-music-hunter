import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Fragment, useEffect, useState } from "react";

import { api } from "../api/client";
import {
  CLASSIFICATIONS, PROBLEM_CLASSIFICATIONS,
  type AnalysisResult, type Classification, type ResultSortKey, type SortOrder,
} from "../api/types";
import { CLASSIFICATION_LABELS, formatBitrate, formatBytes, formatNumber } from "../format";
import { ClassificationBadge } from "./Badges";

const PAGE_SIZE = 50;
const SEARCH_DELAY_MS = 300;

// Valor del desplegable de clasificación que equivale a "Solo problemas"
const PROBLEMS_OPTION = "problems";

// La columna "Clasificación" ordena por gravedad: fake, sospechoso, error, legítimo
const COLUMNS: { key: ResultSortKey; label: string; hideOnMobile: boolean; numeric?: boolean }[] = [
  { key: "file_name", label: "Archivo", hideOnMobile: false },
  { key: "severity", label: "Clasificación", hideOnMobile: false },
  { key: "format", label: "Formato", hideOnMobile: true },
  { key: "bitrate", label: "Bitrate", hideOnMobile: true, numeric: true },
  { key: "cutoff_frequency", label: "Corte", hideOnMobile: true, numeric: true },
  { key: "spectral_presence", label: "Presencia 18-22 kHz", hideOnMobile: true, numeric: true },
];

interface Props {
  jobId: string;
  /** Clasificaciones a mostrar; una lista vacía muestra todas. */
  classification: Classification[];
  onClassificationChange: (classification: Classification[]) => void;
}

/**
 * Resultados de un trabajo. Los filtros, el orden y la paginación se resuelven
 * en el servidor, así que se aplican a todos los resultados y no solo a la
 * página visible. Por defecto se muestran primero los problemas.
 */
export function ResultsTable({ jobId, classification, onClassificationChange }: Props) {
  const [format, setFormat] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [sort, setSort] = useState<{ key: ResultSortKey; order: SortOrder }>({ key: "severity", order: "asc" });
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), SEARCH_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [search]);

  // Al cambiar cualquier filtro o el orden volvemos a la primera página
  const classificationKey = classification.join(",");
  useEffect(() => setOffset(0), [classificationKey, format, debouncedSearch, sort]);

  const filters = {
    classification,
    format: format || undefined,
    q: debouncedSearch || undefined,
    sort: sort.key,
    order: sort.order,
    offset,
    limit: PAGE_SIZE,
  };
  const results = useQuery({
    queryKey: ["results", jobId, filters],
    queryFn: () => api.results(jobId, filters),
    placeholderData: keepPreviousData,
  });

  const rows = results.data?.items ?? [];
  const total = results.data?.total ?? 0;

  const toggleSort = (key: ResultSortKey) =>
    setSort((current) => ({
      key,
      order: current.key === key && current.order === "asc" ? "desc" : "asc",
    }));

  return (
    <div className="card">
      <div className="row" style={{ marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>Resultados</h2>
        <span className="muted small" aria-live="polite">{total} {total === 1 ? "archivo" : "archivos"}</span>
        <span className="spacer" />
        <select aria-label="Filtrar por clasificación" value={classificationToOption(classification)}
          onChange={(e) => onClassificationChange(optionToClassification(e.target.value))}>
          <option value="">Todas las clasificaciones</option>
          <option value={PROBLEMS_OPTION}>Solo problemas</option>
          {CLASSIFICATIONS.map((value) => <option key={value} value={value}>{CLASSIFICATION_LABELS[value]}</option>)}
        </select>
        <select aria-label="Filtrar por formato" value={format} onChange={(e) => setFormat(e.target.value)}>
          <option value="">Todos los formatos</option>
          <option value="flac">FLAC</option>
          <option value="wav">WAV</option>
          <option value="mp3">MP3</option>
        </select>
        <input type="search" placeholder="Buscar por nombre…" aria-label="Buscar por nombre"
          value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {results.isError && <div className="notice notice-error">{results.error.message}</div>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {COLUMNS.map((column) => (
                <th key={column.key}
                  className={[column.hideOnMobile && "hide-mobile", column.numeric && "number"].filter(Boolean).join(" ")}
                  aria-sort={sort.key === column.key ? (sort.order === "asc" ? "ascending" : "descending") : "none"}>
                  <button onClick={() => toggleSort(column.key)}>
                    {column.label} {sort.key === column.key ? (sort.order === "asc" ? "▲" : "▼") : ""}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((result, index) => {
              const isExpanded = expanded === result.file_path;
              const detailId = `detalle-${index}`;
              const toggleDetail = () => setExpanded(isExpanded ? null : result.file_path);
              return (
                <Fragment key={result.file_path}>
                  {/* Toda la fila responde al ratón; el botón da el acceso con teclado */}
                  <tr className="clickable" onClick={toggleDetail}>
                    <td className="file-name">
                      <button type="button" className="row-toggle" aria-expanded={isExpanded} aria-controls={detailId}
                        onClick={(event) => {
                          // Sin esto, el clic llegaría también a la fila y el detalle se alternaría dos veces
                          event.stopPropagation();
                          toggleDetail();
                        }}>
                        {result.file_name}
                      </button>
                      <div className="small muted result-reason">{result.reason}</div>
                    </td>
                    <td>
                      <ClassificationBadge value={result.classification} />
                      {/* En móvil, la frecuencia de corte sustituye a las columnas ocultas */}
                      <div className="small muted mobile-only">{formatNumber(result.cutoff_frequency, "Hz", 0)}</div>
                    </td>
                    <td className="hide-mobile">{result.format.slice(1).toUpperCase()}</td>
                    <td className="hide-mobile number">{formatBitrate(result.bitrate)}</td>
                    <td className="hide-mobile number">{formatNumber(result.cutoff_frequency, "Hz", 0)}</td>
                    <td className="hide-mobile number">{formatNumber(result.spectral_presence, "%")}</td>
                  </tr>
                  {isExpanded && (
                    <tr id={detailId}>
                      <td colSpan={COLUMNS.length} className="detail-cell"><ResultDetail result={result} /></td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
            {rows.length === 0 && !results.isPending && (
              <tr><td colSpan={COLUMNS.length} className="muted">No hay resultados con estos filtros.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {total > PAGE_SIZE && (
        <div className="pagination">
          <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Anterior</button>
          <span className="small muted">
            {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} de {total}
          </span>
          <button disabled={offset + PAGE_SIZE >= total} onClick={() => setOffset(offset + PAGE_SIZE)}>Siguiente</button>
        </div>
      )}
    </div>
  );
}

function ResultDetail({ result }: { result: AnalysisResult }) {
  const above20k = result.has_content_above_20k === null ? "—" : result.has_content_above_20k ? "Sí" : "No";
  return (
    <div>
      <p style={{ margin: 0 }}><strong>{CLASSIFICATION_LABELS[result.classification]}:</strong> {result.reason}</p>
      <p className="small muted" style={{ margin: "4px 0 0", wordBreak: "break-all" }}>{result.file_path}</p>
      <dl className="metrics">
        <Metric label="Formato" value={result.format.slice(1).toUpperCase()} />
        <Metric label="Bitrate" value={formatBitrate(result.bitrate)} />
        <Metric label="Sample rate" value={formatNumber(result.sample_rate, "Hz", 0)} />
        <Metric label="Frecuencia de corte" value={formatNumber(result.cutoff_frequency, "Hz", 0)} />
        <Metric label="Presencia espectral (18-22 kHz)" value={formatNumber(result.spectral_presence, "%")} />
        <Metric label="Energía en altas frecuencias" value={formatNumber(result.high_freq_energy, "dB")} />
        <Metric label="Contenido por encima de 20 kHz" value={above20k} />
        <Metric label="Rango dinámico" value={formatNumber(result.dynamic_range, "dB")} />
        <Metric label="Duración" value={formatNumber(result.duration, "s", 0)} />
        <Metric label="Tamaño" value={formatBytes(result.file_size)} />
      </dl>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

/** Valor del desplegable que corresponde a la lista de clasificaciones filtradas. */
function classificationToOption(classification: Classification[]): string {
  if (classification.length === 0) return "";
  if (classification.length === 1) return classification[0];
  const isProblems = PROBLEM_CLASSIFICATIONS.every((value) => classification.includes(value))
    && classification.length === PROBLEM_CLASSIFICATIONS.length;
  return isProblems ? PROBLEMS_OPTION : "";
}

function optionToClassification(option: string): Classification[] {
  if (option === "") return [];
  if (option === PROBLEMS_OPTION) return PROBLEM_CLASSIFICATIONS;
  return [option as Classification];
}
