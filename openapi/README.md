# FREKCORE OpenAPI contract

`frekcore.openapi.json` is generated from the existing FastAPI application. It is not
hand-authored and it does not cause Swagger/OpenAPI to be public in production.

```bash
python scripts/export_openapi.py
python scripts/export_openapi.py --check
```

The second command is the CI drift check. The generator uses local import-only defaults,
does not start Uvicorn, and does not connect to MongoDB. Review the generated identity,
moment, FK, notary, passport, ecosystem, Staff and Admin contracts before committing it.
