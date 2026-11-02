"""Create reproducible, GitHub-safe public case fixtures.

Requires authorized local case CSVs under --source-dir; it does NOT publish the
restricted source policy manual. Four business tables are copied unchanged,
while customers and orders are transformed deterministically. The policy PDF
is an explicitly synthetic demo manual, not the restricted source manual.

Run from repository root:
    python scripts/prepare_public_data.py --source-dir data --out-dir data_public
"""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

SRC = ("categories", "products", "promotions", "order_items", "customers", "orders")
SAFE_UNCHANGED = ("categories", "products", "promotions", "order_items")


def load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"Missing header in {path}")
        return list(reader.fieldnames), list(reader)


def save(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def anonymize_customers(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []
    for r in rows:
        cid = r["customer_id"]
        # FK is kept to preserve the testable relational dataset, but name,
        # phone, email and city are replaced with synthetic details.
        result.append({**r, "name": f"Cliente fictício {int(cid):03d}",
                       "phone": "0000000000", "email": f"customer{int(cid):03d}@example.test",
                       "city": "Cidade Demonstrativa"})
    return result


def anonymize_orders(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {**r, "tracking_code": f"DEMO-{int(r['order_id']):04d}" if r.get("tracking_code", "").strip() else "",
         "notes": ""}
        for r in rows
    ]


def main() -> int:
    p = argparse.ArgumentParser(description="Prepare sanitized public Artefact case files")
    p.add_argument("--source-dir", type=Path, default=Path("data"))
    p.add_argument("--out-dir", type=Path, default=Path("data_public"))
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    src = (root / args.source_dir).resolve()
    out = (root / args.out_dir).resolve()
    if src == out or src in out.parents:
        raise ValueError("Output must not equal or be nested within the private source directory")
    if not (root / "demo_data" / "políticas_da_loja.pdf").exists():
        raise FileNotFoundError("Synthetic demonstration policy PDF missing")
    for name in SRC:
        if not (src / f"{name}.csv").is_file():
            raise FileNotFoundError(f"Missing original source CSV: {name}.csv")
    out.mkdir(parents=True, exist_ok=True)
    tables = {name: load(src / f"{name}.csv") for name in SRC}
    for name in SAFE_UNCHANGED:
        fields, rows = tables[name]
        save(out / f"{name}.csv", fields, rows)
    fields, rows = tables["customers"]
    sanitized_customers = anonymize_customers(rows)
    save(out / "customers.csv", fields, sanitized_customers)
    fields, rows = tables["orders"]
    sanitized_orders = anonymize_orders(rows)
    save(out / "orders.csv", fields, sanitized_orders)
    # The original manual has a restricted/internal marking: never copy it.
    shutil.copyfile(root / "demo_data" / "políticas_da_loja.pdf", out / "políticas_da_loja.pdf")

    # Export-time checks prevent re-identification via customer fields and
    # prevent broken relational links in the publishable snapshot.
    customer_ids = {r["customer_id"] for r in sanitized_customers}
    order_ids = {r["order_id"] for r in sanitized_orders}
    product_ids = {r["product_id"] for r in tables["products"][1]}
    category_ids = {r["category_id"] for r in tables["categories"][1]}
    for r in sanitized_customers:
        if not r["email"].endswith("@example.test") or r["phone"] != "0000000000":
            raise AssertionError("Unredacted customer record")
    for r in sanitized_orders:
        assert r["customer_id"] in customer_ids
        assert not r["notes"]
        assert not r["tracking_code"] or r["tracking_code"].startswith("DEMO-")
    for r in tables["products"][1]:
        assert r["category_id"] in category_ids
    for r in tables["promotions"][1]:
        assert r["product_id"] in product_ids
    for r in tables["order_items"][1]:
        assert r["product_id"] in product_ids and r["order_id"] in order_ids
    print("Public case dataset generated and FK/privacy checks passed:")
    for name in SRC:
        print(f"  {name}: {len(tables[name][1])} rows")
    print("  políticas_da_loja.pdf: 1-page synthetic demonstration (NOT the original)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
