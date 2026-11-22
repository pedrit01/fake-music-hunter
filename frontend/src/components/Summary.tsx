import { CLASSIFICATIONS, type Classification } from "../api/types";
import { CLASSIFICATION_LABELS, formatPercent } from "../format";

interface Props {
  counts: Record<Classification, number>;
  total: number;
  /** Filtro actual de la tabla; una tarjeta está activa si es la única clasificación filtrada. */
  selected: Classification[];
  onSelect: (classification: Classification[]) => void;
}

/**
 * Totales por clasificación. Al pulsar una tarjeta se filtra la tabla por esa
 * clasificación, y al volver a pulsarla se quita el filtro. Las tarjetas sin
 * resultados se atenúan para que destaquen las que sí tienen.
 */
export function Summary({ counts, total, selected, onSelect }: Props) {
  return (
    <div className="summary">
      {CLASSIFICATIONS.map((classification) => {
        const count = counts[classification] ?? 0;
        const isSelected = selected.length === 1 && selected[0] === classification;
        const classes = ["summary-item", `summary-${classification}`];
        if (isSelected) classes.push("selected");
        if (count === 0) classes.push("empty");
        return (
          <button
            key={classification}
            className={classes.join(" ")}
            aria-pressed={isSelected}
            onClick={() => onSelect(isSelected ? [] : [classification])}
          >
            {CLASSIFICATION_LABELS[classification]}
            <strong>{count}</strong>
            <span className="small">{formatPercent(count, total)}</span>
          </button>
        );
      })}
    </div>
  );
}
