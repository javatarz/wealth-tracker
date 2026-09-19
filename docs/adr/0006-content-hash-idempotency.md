# Statement reimports are de-duplicated by content hash

Every Transaction derived from a statement carries a fingerprint over its identifying fields (date, folio, scheme, type, units, amount). Reimporting an overlapping statement merges cleanly by skipping identical fingerprints, which is correct for the common case of a monthly statement imported quarterly.

## Considered Options

- **Statement-version replacement**: needed only when an issuer *revises* a statement. Deferred rather than rejected — see the fog on statement revisions.
- **Append with manual de-duplication**: pushes routine correctness work onto the user.

## Consequences

- The fingerprint is derived from parsed output, so parser changes can alter it; it must be stable and versioned deliberately.
- A revision yields two near-identical Transactions with different amounts, so detecting revisions will need its own mechanism later.
