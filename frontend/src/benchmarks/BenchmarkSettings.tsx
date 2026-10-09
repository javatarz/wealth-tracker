import type { ReactNode } from "react";
import { useState } from "react";

import { AssetClassSection } from "./AssetClassSection";
import { BenchmarkPreview } from "./BenchmarkPreview";
import type { AssetClassBenchmark, BenchmarkConfig } from "./benchmarkConfig";
import { InstrumentBenchmarks } from "./InstrumentBenchmarks";
import { useBenchmarkConfig, type ConfigState } from "./useBenchmarkConfig";

export function BenchmarkSettings() {
  const state = useBenchmarkConfig();

  return (
    <section aria-labelledby="settings-heading">
      <h2 id="settings-heading">Benchmark settings</h2>
      {renderView(state.kind, state)}
    </section>
  );
}

type Kind = ConfigState["kind"];
type StateOf<K extends Kind> = Extract<ConfigState, { kind: K }>;
type View<K extends Kind> = (state: StateOf<K>) => ReactNode;

const views: { [K in Kind]: View<K> } = {
  loading: () => (
    <p role="status" className="muted">
      Loading benchmarks…
    </p>
  ),
  error: ({ message }) => (
    <p role="alert" className="callout bad">
      {message}
    </p>
  ),
  ready: ({ config }) => <BenchmarkConfigBody initial={config} />,
};

function renderView<K extends Kind>(kind: K, state: StateOf<K>): ReactNode {
  return views[kind](state);
}

function BenchmarkConfigBody({ initial }: { initial: BenchmarkConfig }) {
  const [config, setConfig] = useState(initial);
  return (
    <>
      <AssetClassList
        config={config}
        onSaved={(assetClass, key) => {
          setConfig(updated(config, assetClass, key));
        }}
      />
      <InstrumentBenchmarks available={config.available} />
      <BenchmarkPreview available={config.available} />
    </>
  );
}

function AssetClassList({
  config,
  onSaved,
}: {
  config: BenchmarkConfig;
  onSaved: (assetClass: string, key: string) => void;
}) {
  return (
    <div className="asset-classes">
      {config.asset_classes.map((view) => (
        <AssetClassSection
          key={view.asset_class}
          assetClass={view.asset_class}
          assignedKey={view.assigned_key}
          overridden={view.overridden}
          available={config.available}
          onSaved={onSaved}
        />
      ))}
    </div>
  );
}

function updated(
  config: BenchmarkConfig,
  assetClass: string,
  key: string,
): BenchmarkConfig {
  return {
    ...config,
    asset_classes: config.asset_classes.map((view) =>
      view.asset_class === assetClass ? saved(view, key) : view,
    ),
  };
}

function saved(view: AssetClassBenchmark, key: string): AssetClassBenchmark {
  return { ...view, assigned_key: key, overridden: true };
}
