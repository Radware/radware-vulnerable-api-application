# RVA Deployment Guide

This document explains how to deploy the Radware Vulnerable API (RVA) application using Docker with different database backends optimized for various use cases.

## Deployment Modes

RVA supports three deployment modes, each optimized for different scenarios:

### 1. In-Memory Database (Development/Testing)
- **Use case:** Quick demos, testing, development
- **Workers:** Single worker only
- **Persistence:** None (data lost on restart)
- **Performance:** Fastest startup
- **File:** `docker-compose.memory.yml`

### 2. SQLite Database (Demos/Single Server)
- **Use case:** Persistent demos, single-instance deployments
- **Workers:** Single worker (SQLite has limited concurrency)
- **Persistence:** Yes (volume-backed)
- **Performance:** Good for moderate load
- **File:** `docker-compose.sqlite.yml`

### 3. PostgreSQL Database (Production/Multi-Worker)
- **Use case:** High-load demos, production deployments
- **Workers:** Multiple workers (configurable, default: 4)
- **Persistence:** Yes (PostgreSQL volume)
- **Performance:** Best for high concurrency
- **File:** `docker-compose.rva-db.yml`

## Version v1.2.2 Notes

- **Default image:** The compose files now default to `razor29/rva:latest`. Override with `RVA_IMAGE` if you want a custom tag or registry.
- **SQL injection demos:** The `/api/products/search` and `/api/users/{userId}/orders/{orderId}/apply-coupon` endpoints include intentional SQL injection behavior. For Postgres-specific payloads (e.g., `ILIKE`, `pg_sleep`), use **PostgreSQL mode** (`docker-compose.rva-db.yml`) or `DB_MODE=external` with a PostgreSQL `DB_URL`. SQLite and in-memory modes are read-only but do not support Postgres-only payloads.

## Quick Start

### In-Memory Mode
```bash
# Start with in-memory database
docker-compose -f docker-compose.memory.yml up -d

# Access the application
curl http://localhost:8060
```

### SQLite Mode
```bash
# Start with SQLite database
docker-compose -f docker-compose.sqlite.yml up -d

# Access the application
curl http://localhost:8060

# Data persists in the rva-sqlite-data volume
```

### PostgreSQL Mode (Recommended for Production)
```bash
# Start PostgreSQL + app with multiple workers
docker-compose -f docker-compose.rva-db.yml up -d

# Access the application
curl http://localhost:8060

# Check that workers are running
docker logs rva-app
```

## Configuration

### Environment Variables

You can customize deployments using environment variables:

```bash
# Change the port
export RVA_PORT=8080

# Change worker count (PostgreSQL mode only)
export UVICORN_WORKERS=8

# Change database credentials (PostgreSQL mode)
export POSTGRES_USER=myuser
export POSTGRES_PASSWORD=mypassword
export POSTGRES_DB=mydb

# Use custom image
export RVA_IMAGE=myregistry/rva:v1.2.2
```

Then start with:
```bash
docker-compose -f docker-compose.rva-db.yml up -d
```

### Performance Tuning

#### Worker Count Recommendations

For **PostgreSQL mode**, adjust workers based on your needs:

- **Light load (demos):** 2-4 workers
  ```bash
  UVICORN_WORKERS=2 docker-compose -f docker-compose.rva-db.yml up -d
  ```

- **Medium load:** 4-8 workers
  ```bash
  UVICORN_WORKERS=4 docker-compose -f docker-compose.rva-db.yml up -d
  ```

- **Heavy load:** 8-16 workers
  ```bash
  UVICORN_WORKERS=8 docker-compose -f docker-compose.rva-db.yml up -d
  ```

**Important:** 
- Memory mode and SQLite mode MUST use single worker (UVICORN_WORKERS=1)
- The worker count is automatically set correctly in the compose files

## Building the Image

Build the RVA image:

```bash
# Build with default tag
docker build -t razor29/rva:latest .

# Build with custom tag
docker build -t myregistry/rva:v1.2.2 .

# Use the custom image
RVA_IMAGE=myregistry/rva:v1.2.2 docker-compose -f docker-compose.rva-db.yml up -d
```

## Database Management

### Reset Database (PostgreSQL Mode)

To completely reset the database:

```bash
# Stop services
docker-compose -f docker-compose.rva-db.yml down

# Remove database volume
docker volume rm rva-pgdata

# Restart (will reinitialize)
docker-compose -f docker-compose.rva-db.yml up -d
```

### Reset Database (SQLite Mode)

```bash
# Stop service
docker-compose -f docker-compose.sqlite.yml down

# Remove database volume
docker volume rm rva-sqlite-data

# Restart (will reinitialize)
docker-compose -f docker-compose.sqlite.yml up -d
```

### Backup Database (PostgreSQL Mode)

```bash
# Backup
docker exec rva-db pg_dump -U rva rva > rva_backup_$(date +%Y%m%d).sql

# Restore
docker exec -i rva-db psql -U rva rva < rva_backup_20231217.sql
```

## Monitoring

### Check Application Health

```bash
# Check if application is responding
curl http://localhost:8060/

# Check API documentation
curl http://localhost:8060/docs

# Check application logs
docker logs rva-app

# Check database logs (PostgreSQL mode)
docker logs rva-db
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats rva-app rva-db

# Check worker processes
docker exec rva-app ps aux | grep uvicorn
```

## Troubleshooting

### Common Issues

#### Issue: "AttributeError: 'SQLiteBackend' object has no attribute 'db_users_by_username'"

**Solution:** This is fixed in the latest version. Make sure you're using the updated code that includes dictionary-like proxies.

#### Issue: "duplicate key value violates unique constraint"

**Solution:** Multiple workers trying to initialize simultaneously. This is fixed by:
- The advisory lock mechanism (enabled by default)
- Checking if database is already initialized before seeding

#### Issue: Slow performance with multiple workers

**Solution:** 
- Make sure you're using PostgreSQL mode, not SQLite or memory mode
- Increase worker count: `UVICORN_WORKERS=8`
- Check database connection pool settings in the code

#### Issue: Database connection errors

**Solution:**
```bash
# Check if database is healthy
docker-compose -f docker-compose.rva-db.yml ps

# Check database logs
docker logs rva-db

# Restart services
docker-compose -f docker-compose.rva-db.yml restart
```

## Advanced Configuration

### Custom Database URL

You can connect to an external PostgreSQL database:

```bash
# Create a custom docker-compose file or use environment variables
DB_MODE=external \
DB_URL=postgresql+psycopg2://user:pass@external-db-host:5432/dbname \
UVICORN_WORKERS=4 \
docker-compose -f docker-compose.rva-db.yml up -d
```

### Disable Auto-Seeding

If you want to manage data manually:

```bash
# Disable automatic data seeding
docker run -e DB_SKIP_AUTO_SEED=true -e DB_MODE=external -e DB_URL=... razor29/rva:latest
```

## Architecture Notes

### Why Different Modes?

1. **In-Memory:** Fastest for ephemeral testing, no I/O overhead
2. **SQLite:** Good balance for single-server deployments, but limited concurrent write performance
3. **PostgreSQL:** Best for production with multiple workers, supports concurrent operations

### Worker Architecture

- Each Uvicorn worker is a separate process
- Workers share the database connection pool (PostgreSQL mode)
- Advisory locks prevent initialization race conditions
- Connection pooling ensures efficient database access

## Support

For issues, see:
- Application logs: `docker logs rva-app`
- Database logs: `docker logs rva-db`
- Health check: `curl http://localhost:8060/`
