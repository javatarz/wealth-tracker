import { overlayGeometry, VIEW_BOX, type OverlayLine } from "./overlayGeometry";

export function OverlayChart({ lines }: { lines: OverlayLine[] }) {
  const geometry = overlayGeometry(lines);

  return (
    <figure className="overlay">
      <svg
        viewBox={VIEW_BOX}
        role="img"
        aria-label="Growth with benchmark overlay"
      >
        {geometry.map((line) => (
          <path key={line.key} className="line" d={line.path} />
        ))}
      </svg>
      <figcaption className="legend">
        {lines.map((line) => (
          <span key={line.key} className="legend-item">
            {line.name}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}
