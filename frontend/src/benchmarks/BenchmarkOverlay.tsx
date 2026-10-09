import { useState, type ReactNode } from "react";

import { OverlayChart } from "./OverlayChart";
import { useBenchmarkReturns, type OverlayState } from "./useBenchmarkReturns";

export function BenchmarkOverlay({
  benchmark,
  name,
  from,
  to,
}: {
  benchmark: string;
  name: string;
  from: string;
  to: string;
}) {
  const [shown, setShown] = useState(true);

  return (
    <section aria-labelledby="overlay-heading" className="overlay-panel">
      <h3 id="overlay-heading">Benchmark overlay</h3>
      <label className="toggle">
        <input
          type="checkbox"
          checked={shown}
          onChange={(event) => {
            setShown(event.target.checked);
          }}
        />
        Show benchmark line
      </label>
      {shown && (
        <OverlayBody benchmark={benchmark} name={name} from={from} to={to} />
      )}
    </section>
  );
}

function OverlayBody({
  benchmark,
  name,
  from,
  to,
}: {
  benchmark: string;
  name: string;
  from: string;
  to: string;
}) {
  const state = useBenchmarkReturns(benchmark, from, to);
  return renderView(state.kind, state, { benchmark, name });
}

type Kind = OverlayState["kind"];
type StateOf<K extends Kind> = Extract<OverlayState, { kind: K }>;
type View<K extends Kind> = (
  state: StateOf<K>,
  line: { benchmark: string; name: string },
) => ReactNode;

const views: { [K in Kind]: View<K> } = {
  loading: (_state, { name }) => (
    <p role="status" className="muted">
      Loading {name}…
    </p>
  ),
  unavailable: (_state, { name }) => (
    <p role="alert" className="callout bad">
      No price history for {name} yet.
    </p>
  ),
  ready: ({ points }, line) => (
    <OverlayChart lines={[{ key: line.benchmark, name: line.name, points }]} />
  ),
};

function renderView<K extends Kind>(
  kind: K,
  state: StateOf<K>,
  line: { benchmark: string; name: string },
): ReactNode {
  return views[kind](state, line);
}
