# Market data comes from first-party Indian sources

Mutual fund NAV comes from AMFI's own files — `NAVAll.txt` for current NAV, the date-range history report for backfill. Equity EOD comes from NSE's UDiFF bhavcopy plus its `EQUITY_L.csv` master. Benchmark index history comes from NSE Indices' TRI export. Gold uses IBJA rates for physical metal and AMFI NAV for MF wrappers; crypto uses CoinGecko for INR valuation.

## Considered Options

- **Community mirrors as the base case** (`mfapi.in`, `tigzig`): convenient, but unofficial. The risk of a source disappearing is exactly what the provider interface in ADR 0010 exists to absorb, so mirrors are fallbacks rather than the primary.
- **Yahoo and other unofficial equity APIs**: no ISIN, and tickers change.

## Consequences

- **AMFI scheme code is the mutual fund identity key, not ISIN.** ISIN is nullable in AMFI's own live rows; scheme name plus plan and option is not unique (two distinct schemes can share a name); and one scheme-code row can carry up to two ISINs. ISIN is therefore stored as a nullable, changeable *attribute* and used only as the cross-source join. This constrains the still-open decision on Instrument identity.
- Benchmark series come from the index provider rather than a fund proxy, so index history can be dividend-inclusive (TRI).
- A mirror to fall back on is a standing requirement, not a nicety, for every data kind.
