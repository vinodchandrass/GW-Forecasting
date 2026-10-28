#!/usr/bin/env python3
"""Compare generated aggregate CSV outputs against a separate frozen reference checkout."""
import argparse
import csv
import math
from pathlib import Path

def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)

def equal(a, b, atol, rtol):
    if a == b:
        return True
    try:
        x, y = float(a), float(b)
        return math.isfinite(x) and math.isfinite(y) and math.isclose(x, y, abs_tol=atol, rel_tol=rtol)
    except (ValueError, TypeError):
        return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reference", required=True, type=Path)
    p.add_argument("--generated", required=True, type=Path)
    p.add_argument("--atol", type=float, default=1e-9)
    p.add_argument("--rtol", type=float, default=1e-8)
    a = p.parse_args()
    ref = a.reference.resolve()
    gen = a.generated.resolve()
    if ref == gen:
        p.error("Reference and generated directories must differ")
    if not (ref / "paper-a-five-state").is_dir() or not (gen / "paper-a-five-state").is_dir():
        p.error("Both directories must be repository roots containing paper-a-five-state/")
    paths = sorted((ref / "paper-a-five-state").glob("*/outputs/*.csv"))
    if not paths:
        p.error("No reference aggregate CSV files found")
    failed = 0
    for src in paths:
        rel = src.relative_to(ref)
        dest = gen / rel
        if not dest.is_file():
            print(f"MISSING {rel}")
            failed += 1
            continue
        try:
            cols1, rows1 = read_csv(src)
            cols2, rows2 = read_csv(dest)
            if cols1 != cols2 or len(rows1) != len(rows2):
                print(f"FAIL schema/row count {rel}")
                failed += 1
                continue
            mismatches = sum(
                not equal(r1[c], r2[c], a.atol, a.rtol)
                for r1, r2 in zip(rows1, rows2)
                for c in cols1
            )
            if mismatches:
                print(f"FAIL {rel}: {mismatches} differing cells")
                failed += 1
            else:
                print(f"PASS {rel}: {len(rows1)} rows")
        except (OSError, UnicodeError, csv.Error) as e:
            print(f"ERROR {rel}: {e}")
            failed += 1
    print(f"Compared {len(paths)} reference CSVs; failed {failed}")
    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
