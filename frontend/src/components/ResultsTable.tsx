import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Fragment, useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import { CLASSIFICATIONS, type AnalysisResult, type Classification } from "../api/types";
import { CLASSIFICATION_LABELS, formatBitrate, formatBytes, formatNumber } from "../format";
import { ClassificationBadge } from "./Badges";

const PAGE_SIZE = 50;
const SEARCH_DELAY_MS = 300;

type SortKey = "file_name" | "classification" | "format" | "bitrate" | "cutoff_frequency" | "spectral_presence";

const COLUMNS: { key: SortKey; label: string; hideOnMobile: boolean }[] = [
  { key: "file_name", label: "Archivo", hideOnMobile: false },
  { key: "classification", label: "Clasificación", hideOnMobile: false },
  { key: "format", label: "Formato", hideOnMobile: true },
  { key: "bitrate", label: "Bitrate", hideOnMobile: true },
  { key: "cutoff_frequency", label: "Corte", hideOnMobile: true },
  { key: "spectral_presence", label: "Presencia 18-22 kHz", hideOnMobile: true },
];

interface Props {
  jobId: string;
  classification: Classification | undefined;
  onClassificationChange: (classification: Classification | undefined) => void;
}

/**
 * Resultados de un trabajo. Los filtros y la paginación se resuelven en el
 * servidor; la ordenación se aplica a la página cargada.
 */
export function ResultsTable({ jobId, classification, onClassificationChange }: Props) {
  const [format, setFormat] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [offset, setOffset] = useState(0);
  const [sort, setSort] = useState<{ key: SortKey; ascending: boolean }>({ key: "file_name", ascending: true });
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), SEARCH_DELAY_MS);
    return () => window.clearTimeout(timer);
  }, [search]);

  // Al cambiar cualquier filtro volvemos a la primera página
  useEffect(() => setOffset(0), [classification, format, debouncedSearch]);

  const filters = { classification, format: format || undefined, q: debouncedSearch || undefined, offset, limit: PAGE_SIZE };
  const results = useQuery({
    queryKey: ["results", jobId, filters],
    queryFn: () => api.results(jobId, filters),
    placeholderData: keepPreviousData,
  });

  const rows = useMemo(() => sortRows(results.data?.items ?? [], sort.key, sort.ascending), [results.data, sort]);
  const total = results.data?.total ?? 0;

  const toggleSort = (key: SortKey) =>
    setSort((current) => ({ key, ascending: current.key === key ? !current.ascending : true }));

  return (
    <div className="card">
      <div className="row" style={{ marginBottom: 12 }}>
        <h2 style={{ margin: 0 }}>Resultados</h2>
        <span className="muted small" aria-live="polite">{total} {total === 1 ? "archivo" : "archivos"}</span>
        <span className="spacer" />
        <select aria-label="Filtrar por clasificación" value={classification ?? ""}
          onChange={(e) => onClassificationChange((e.target.value || undefined) as Classification | undefined)}>
          <option value="">Todas las clasificaciones</option>
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
                <th key={column.key} className={column.hideOnMobile ? "hide-mobile" : ""}
                  aria-sort={sort.key === column.key ? (sort.ascending ? "ascending" : "descending") : "none"}>
                  <button onClick={() => toggleSort(column.key)}>
                    {column.label} {sort.key === column.key ? (sort.ascending ? "▲" : "▼") : ""}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((result) => {
              const isExpanded = expanded === result.file_path;
              return (
                <Fragment key={result.file_path}>
                  <tr className="clickable" aria-expanded={isExpanded}
                    onClick={() => setExpanded(isExpanded ? null : result.file_path)}>
                    <td className="file-name">
                      {result.file_name}
                      <div className="small muted">{result.reason}</div>
                    </td>
                    <td><ClassificationBadge value={result.classification} /></td>
                    <td className="hide-mobile">{result.format.slice(1).toUpperCase()}</td>
                    <td className="hide-mobile number">{formatBitrate(result.bitrate)}</td>
                    <td className="hide-mobile number">{formatNumber(result.cutoff_frequency, "Hz", 0)}</td>
                    <td className="hide-mobile number">{formatNumber(result.spectral_presence, "%")}</td>
                  </tr>
                  {isExpanded && (
                    <tr>
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

function sortRows(rows: AnalysisResult[], key: SortKey, ascending: boolean): AnalysisResult[] {
  const direction = ascending ? 1 : -1;
  return [...rows].sort((a, b) => {
    const left = a[key];
    const right = b[key];
    // Los valores ausentes siempre al final
    if (left === null) return 1;
    if (right === null) return -1;
    if (typeof left === "number" && typeof right === "number") return (left - right) * direction;
    return String(left).localeCompare(String(right), "es") * direction;
  });
}
