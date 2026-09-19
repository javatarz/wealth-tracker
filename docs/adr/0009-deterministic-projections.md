# Deterministic, pluggable Projection Strategies

Goal projections use deterministic growth — a fixed CAGR, or an average growth rate over a trailing *n* years — chosen by the user from a set of Projection Strategies. Monte Carlo simulation is deferred.

## Considered Options

- **Monte Carlo from day one**: more honest about uncertainty, but heavier to build and harder for a user to reason about. The Goal model is identical either way, so it can be added as another strategy later.

## Consequences

- The Projection Strategy is a user-visible choice, so its name, parameters, and underlying assumptions must be shown alongside every projection.
- A deterministic projection is drawn as a single line, which can read as certainty; the UI must not imply more confidence than the method has.
