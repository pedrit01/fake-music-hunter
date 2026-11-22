import { CLASSIFICATIONS, type Classification } from "../api/types";
import { CLASSIFICATION_LABELS, formatPercent } from "../format";

interface Props {
  counts: Record<Classification, number>;
  total: number;
  selected: Classification | undefined;
  onSelect: (classification: Classification | undefined) => void;
}

/** Totales por clasificación. Al pulsar una tarjeta se filtra la tabla. */
export function Summary({ counts, total, selected, onSelect }: Props) {
  return (
    <div className="summary">
      {CLASSIFICATIONS.map((classification) => {
        const count = counts[classification] ?? 0;
        const isSelected = selected === classification;
        return (
          <button
            key={classification}
            className={`summary-item summary-${classification} ${isSelected ? "selected" : ""}`}
            aria-pressed={isSelected}
            onClick={() => onSelect(isSelected ? undefined : classification)}
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
