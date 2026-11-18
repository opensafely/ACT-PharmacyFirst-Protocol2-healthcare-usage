
"""
Apply statistical disclosure control to monthly PF consultation counts.

Input: output/pf_consultations_by_month.csv
Output: output/pf_consultations_by_month_release.csv

Rules:
- Missing values are retained.
- Zero counts are retained.
- Counts of 1–7 are replaced with [REDACTED].
- Counts greater than 7 are rounded to the nearest 5.

"""

from decimal import Decimal, InvalidOperation
from pathlib import Path
import pandas as pd

INPUT_FILE = Path("output/pf_consultations_by_month.csv")
OUTPUT_FILE = Path("output/pf_consultations_by_month_release.csv")

REDACTED = "[REDACTED]"
SUPPRESSION_THRESHOLD = 7
ROUNDING_BASE = 5

DATE_COLUMN = "start_date"

COUNT_COLUMNS = [
    "num_pf_cons_uti",
    "num_pf_cons_sinusitis",
    "num_pf_cons_ibite",
    "num_pf_cons_otitismedia",
    "num_pf_cons_sorethroat",
    "num_pf_cons_shingles",
    "num_pf_cons_impetigo",
]


# Suppression function
def suppress_count(value):
    """Suppress and round non-negative integer counts."""
    if pd.isna(value):
        return value

    text = str(value).strip()

    if text in ("", "."):
        return value

    try:
        number = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"Invalid count value: {value}") from None

    if (
        not number.is_finite()
        or number < 0
        or number != number.to_integral_value()
    ):
        raise ValueError(f"Count must be a non-negative integer: {value}")

    count = int(number)

    if count == 0:
        return 0

    if count <= SUPPRESSION_THRESHOLD:
        return REDACTED

    return ((count + ROUNDING_BASE // 2) // ROUNDING_BASE) * ROUNDING_BASE

def main():

    if not INPUT_FILE.is_file():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(
        INPUT_FILE,
        dtype=str,
        keep_default_na=False,
    )

    expected_columns = {DATE_COLUMN, *COUNT_COLUMNS}

    missing_columns = expected_columns - set(df.columns)
    extra_columns = set(df.columns) - expected_columns

    if missing_columns or extra_columns:
        raise ValueError(
            "Unexpected column structure. "
            f"Missing columns: {sorted(missing_columns)}; "
            f"Extra columns: {sorted(extra_columns)}"
        )

    print(f"Input file: {INPUT_FILE}")
    print(f"Number of months: {len(df):,}")

    release_df = df.copy()

    for column in COUNT_COLUMNS:
        try:
            release_df[column] = df[column].map(suppress_count)
        except ValueError as exc:
            raise ValueError(f"Invalid values in column {column}: {exc}") from None

    release_df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
