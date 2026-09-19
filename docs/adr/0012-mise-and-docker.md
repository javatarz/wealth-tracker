# mise for the toolchain, Docker for the packaged runtime

Development uses `mise` to pin Python and Node versions, so contributors and CI agree on toolchains. Packaged runs use Docker, with the database on a mounted volume. This keeps development and packaged data separate, and gives users a single command that runs the tool without installing a Python or Node environment first.

## Consequences

- The database lives outside the image, so schema migration and backup are user-visible concerns rather than container details.
- Users who cannot or will not run Docker need a documented non-Docker path; `mise` alone must remain sufficient to run the application locally.
