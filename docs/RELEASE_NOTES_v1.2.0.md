# Release v1.2.0

This release introduces a new set of infrastructure features and documentation updates for the vulnerable e‑commerce API.  The OpenAPI definition now references version **1.2.0** and new configuration options allow running the application with different database backends.

## Highlights

- **Database backends** can now be selected via the `DB_MODE` environment variable. Supported values are `memory` (default), `sqlite` and `external`.
- **External databases** are configured through the new `DB_URL` variable. SQLite paths are provided via `DB_SQLITE_PATH`.
- **Peer database sync service** allows two instances to synchronize data using `DB_SYNC_PEER` and `DB_SYNC_INTERVAL`.
- **OpenAPI schema** is loaded from `openapi.yaml`, simplifying modifications and keeping `openapi.json` updated automatically.
- **SQLite testing fixtures** improve test coverage and documentation on how to run tests with SQLite.
- **Docker configuration examples** in the README demonstrate using the new database options.
- **Release workflow** (`.github/workflows/release.yml`) builds and publishes Docker images with version tags.

## Upgrade Notes

1. Update your environment variables if you wish to use SQLite or an external database backend.
2. If using Docker, mount a volume for the SQLite file or provide a proper connection string for your external DB.
3. To synchronize data across instances, set `DB_SYNC_PEER` to the base URL of the peer and optionally adjust `DB_SYNC_INTERVAL`.
4. Existing functionality remains compatible when `DB_MODE` is left at its default `memory`.

