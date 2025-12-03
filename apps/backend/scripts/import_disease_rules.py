"""Import disease rules from CSV into the database."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = WORKSPACE_ROOT / "data"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import Base, SessionLocal, engine  # noqa: E402
from models import DiseaseRuleModel  # noqa: E402


def _normalize_tags(raw: str) -> List[str]:
    if not raw:
        return []
    parts = [part.strip() for part in raw.split(";") if part.strip()]
    return [p.lower() for p in parts]


def import_rules(csv_path: Path) -> int:
    Base.metadata.create_all(bind=engine)
    session: Session = SessionLocal()
    try:
        count = 0
        with csv_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                name = row.get("Disease") or row.get("disease")
                if not name:
                    continue
                normalized_name = name.strip()
                tags = _normalize_tags(
                    row.get("Prohibited_Tags") or row.get("prohibited_tags") or ""
                )
                existing = (
                    session.query(DiseaseRuleModel)
                    .filter(DiseaseRuleModel.name == normalized_name)
                    .first()
                )
                if existing:
                    existing.prohibited_tags = tags
                else:
                    session.add(
                        DiseaseRuleModel(name=normalized_name, prohibited_tags=tags)
                    )
                count += 1
        session.commit()
        return count
    finally:
        session.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import disease rules CSV.")
    parser.add_argument(
        "--csv",
        default=str(DATA_DIR / "Disease_rules.csv"),
        help="Path to Disease_rules.csv",
    )
    args = parser.parse_args()
    path = Path(args.csv)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    total = import_rules(path)
    print(f"Imported {total} disease rules.")

