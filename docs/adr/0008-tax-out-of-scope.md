# Tax computation is out of scope

The application records everything tax planning needs — lots, acquisition dates, holding periods, Income amounts and their disposition — but computes no tax. Capital-gains and income-tax calculation, filing support, and liability estimation are all excluded.

## Considered Options

- **Capital-gains report**: tempting, since FIFO lot reduction already exists, but Indian tax constants change every Budget, which makes a computed figure a maintenance liability that is wrong the moment rates move.

## Consequences

- Tax-aware liquidation planning (choosing *which* lot funds a Goal) remains a stated future goal, so per-lot identity and holding periods must be preserved even though nothing consumes them yet.
- When tax logic does arrive, rates and holding-period thresholds must be versioned by Financial Year and user-overridable, never hardcoded.
