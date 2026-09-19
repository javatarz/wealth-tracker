# Market data is online-first, cached, and explicitly refreshed

Prices and NAVs are fetched from an external source, cached locally, and shown with a "last updated" timestamp; if the source is unreachable the application serves stale data and says so. Refresh is triggered by the user rather than a background scheduler, so the application never contacts the network unasked.

## Consequences

- The provider sits behind an interface. Free Indian sources can vanish or change shape, so swapping providers must not touch the domain model.
- Only market data leaves the machine; portfolio data never does. This is part of the privacy posture, not merely a caching policy.
- A background scheduler remains a later addition and must not require reworking the provider boundary.
