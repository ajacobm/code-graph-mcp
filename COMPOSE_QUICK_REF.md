# Quick Reference: Docker Compose & Makefile

## One-Liners for Common Tasks

```bash
# Start development (everything)
make dev-up

# Stop everything
make down

# View logs
make logs

# Backend only (for frontend dev)
make backend-up

# Testing environment
make test-up

# Clean all containers/volumes
make clean

# Check running containers
make ps

# Rebuild images
make rebuild

# View all targets
make help
```

## Environment Profiles

| Profile | Use Case | Command |
|---------|----------|---------|
| default | Development | `make dev-up` |
| test | Testing | `make test-up` |
| backend | Frontend dev | `make backend-up` |
| codespaces | GitHub Codespaces | `make codespaces-up` |
| ghcr | Container registry | `make ghcr-up` |
| multi | Extended services | `make multi-up` |
| validation | CI/validation | `make validation-up` |

## Direct Docker Compose (If Needed)

```bash
# Base only
cd infrastructure
docker-compose up -d

# With test profile
docker-compose -f docker-compose.yml -f profiles/test.yml up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## File Locations

- **Base config**: `infrastructure/docker-compose.yml`
- **Profiles**: `infrastructure/profiles/*.yml`
- **Redis config**: `infrastructure/redis.conf`
- **Makefile**: `./Makefile` (root)
- **Documentation**: `infrastructure/README.md`

---

See `infrastructure/README.md` for detailed documentation.

