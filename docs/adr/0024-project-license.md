# AGPL-3.0 license for Wealth Tracker

The project is published under the GNU Affero General Public License v3.0.

## Decision

AGPL-3.0 is the governing license for all code in this repository.

## Rationale

1. **Privacy ethos demands legal reciprocity.** ADR 0019 establishes that
   portfolio data never leaves the device. AGPL-3.0 extends that protective
   posture to the code: anyone who modifies the software and makes it
   available over a network must share their changes (Section 13, the
   "network clause"). Security fixes, parser improvements, and feature
   work that benefit one deployment must benefit all.

2. **Strong copyleft prevents enclosure.** MIT would permit a company to
   take the project, add telemetry or lock-in, and sell it as a proprietary
   SaaS without contributing anything back — directly contradicting the
   project's privacy-first values.

3. **OSI-approved and standard in the ecosystem.** AGPL is well-understood,
   GitHub-native (60k+ repositories), and compatible with the project's
   permissive dependencies (Python standard library, FastAPI, SQLite,
   React). No licence-policing overhead.

4. **PolyForm/BSL is over-engineered for this project.** Source-available
   licences solve for commercial free-riding at the cost of OSI recognition
   and contributor familiarity. A personal wealth tracker is unlikely to
   attract SaaS competitors; AGPL's protections are sufficient.

## Consequences

- A `LICENSE` file containing the full AGPL-3.0 text lives at the repo root.
- The README's License section now reads "AGPL-3.0".
- Contributors implicitly agree to license their contributions under AGPL-3.0
  (standard inbound = outbound).
- The project can be forked freely; modified versions that are network-accessible
  must publish their source under AGPL-3.0.
- No additional CLA or copyright assignment is required.