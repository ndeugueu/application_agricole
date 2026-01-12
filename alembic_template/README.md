# Alembic Template (per-service)

This folder is a template to add Alembic migrations to each service.

Usage (per service):
1) Copy this folder into the service root (next to main.py and models.py).
   Example:
     services/identity/alembic/
     services/identity/alembic.ini

2) From the service folder, initialize baseline migration:
   set DATABASE_URL=postgresql://.../identity_db
   alembic revision --autogenerate -m "baseline"

3) Apply migrations:
   alembic upgrade head

Environment variables:
- DATABASE_URL: full SQLAlchemy URL for the service database.
- ALEMBIC_TARGET_MODULE: module to import for models (default: models).

Notes:
- Remove Base.metadata.create_all(...) from service main.py once migrations are in place.
- Keep migrations versioned per service.
