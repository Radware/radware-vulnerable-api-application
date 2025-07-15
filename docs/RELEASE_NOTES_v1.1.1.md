# Release Notes - v1.1.1

This version introduces several enhancements and fixes across the vulnerable e-commerce API and demo UI. These notes can be used directly in the GitHub release description.

## Highlights

- **Coupon Management** – Added endpoints and UI support for creating, deleting and applying coupons. Coupons may be marked as protected to demonstrate BFLA scenarios.
- **BOLA Demo Improvements** – Refined checkout flow and profile handling to reliably showcase Broken Object Level Authorization vulnerabilities.
- **Performance and Caching** – Implemented lightweight caching for product listings and enabled gzip/static asset caching to improve demo responsiveness.
- **Dataset Updates** – Expanded pre-populated users and coupons, including additional protected entities used by automated demo traffic.
- **OpenAPI & Documentation** – OpenAPI schema is now loaded from `openapi.yaml` and documentation for the `/docs` endpoint has been updated.
- **Container Defaults** – Docker image now starts the API with a single Uvicorn worker by default for predictable behavior.
- **Miscellaneous Fixes** – Various bug fixes around coupon logic, BOLA selection, and UI interactions.

## Getting Started

1. Build and run the Docker image or start the servers via `run_dev.sh`.
2. Access the API documentation at `http://localhost:8000/docs`.
3. Explore the demo UI at `http://localhost:5001/`.

For details on protected entities and testing guidelines see [PROTECTED_ENTITIES.md](../PROTECTED_ENTITIES.md) and [TESTING.md](../TESTING.md).

