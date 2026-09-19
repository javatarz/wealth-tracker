# No authentication; one instance serves a household

The application ships with no login. It is designed to be run locally by a technical user, and its privacy model is that portfolio data never leaves the machine. Several Household Members' data lives in one instance, separated by a member identifier, but there is no access control between them — the instance is the security boundary.

## Considered Options

- **Per-member logins**: rejected as complexity with no threat-model benefit on a single-user machine.

## Consequences

- Exposure is entirely determined by how the user runs it. Binding to a network interface or placing it behind a reverse proxy removes the safety of the single-machine assumption, so the documentation must say so plainly.
- A future hosted variant is a different product, not a configuration flag.
