"""Export or verify FREKCORE's FastAPI OpenAPI contract without starting the service."""
import argparse
import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
ARTIFACT = ROOT / "openapi" / "frekcore.openapi.json"


def schema() -> dict:
    sys.path.insert(0, str(BACKEND))
    os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
    os.environ.setdefault("DB_NAME", "frekcore_openapi_export")
    os.environ.setdefault("SECRET_KEY", "openapi-export-not-a-runtime-secret")
    os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
    os.environ.setdefault("FREK_ENV", "development")
    os.environ.setdefault("FREK_PUBLIC_DOCS", "false")
    from server import app
    return app.openapi()


def canonical_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail when the committed artifact differs")
    args = parser.parse_args()
    generated = canonical_json(schema())
    if args.check:
        if not ARTIFACT.exists():
            print(f"OpenAPI artifact missing: {ARTIFACT}", file=sys.stderr)
            return 2
        if ARTIFACT.read_text() != generated:
            print("OpenAPI drift detected; run python scripts/export_openapi.py and commit the artifact.", file=sys.stderr)
            return 1
        print("OpenAPI artifact is current")
        return 0
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(generated)
    print(f"Wrote {ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
