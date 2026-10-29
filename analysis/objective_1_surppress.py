"""
OpenSAFELY statistical disclosure control: https://docs.opensafely.org/outputs/sdc/
OpenSAFELY permitted output: https://www.opensafely.org/policies-for-researchers/permitted-outputs-policy/

This script is to surppress the output from objective 1 analysis.
Process the listed "oneway," "twoway," and "threeway" files; exclude "pf_cons_general.csv."

Rules: 
- Missing values ​​are retained; 0 is retained; 
- 1–7 are replaced with [REDACTED]; 
- for all other counts, values ​​are rounded to the nearest 5.

TODO:
1. Check for secondary disclosure within and across tables
2. Check that equivalent totals are consistent across the original tables - any differences after rounding
"""

import argparse
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd


REDACTED = "[REDACTED]"
SUPPRESSION_THRESHOLD = 7
ROUNDING_BASE = 5

CONDITIONS = ("all", "ibite", "impetigo", "otitismedia", "shingles", "sinusitis", "sorethroat", "uti")

CONDITION_COUNT_COLUMNS = tuple("sum" + condition for condition in CONDITIONS)

DATE_COLUMNS = ("date", "index_date_stata")
TABLES = {
    "oneway_date_condition.csv": (("sum",), ("condition",)),
    "oneway_date.csv": (("sum",), DATE_COLUMNS),
}
for subgroup in ("region", "stp", "age_group", "sex", "ethnicity", "imd"):
    TABLES[f"oneway_{subgroup}.csv"] = (("sum",), (subgroup,))

TABLES["twoway_date_condition.csv"] = (CONDITION_COUNT_COLUMNS, DATE_COLUMNS)
for subgroup in ("region", "stp", "age_group", "sex", "ethnicity", "imd"):
    TABLES[f"twoway_{subgroup}_condition.csv"] = (CONDITION_COUNT_COLUMNS, (subgroup,))

for subgroup in ("region", "stp", "age_group", "sex", "ethnicity", "imd"):
    group_column = "region_num" if subgroup == "region" else subgroup
    TABLES[f"threeway_condition_date_{subgroup}.csv"] = (CONDITION_COUNT_COLUMNS, DATE_COLUMNS + (group_column,))


def suppress_count(value):
    """Handle a non-negative integer count; report an error for invalid input."""
    if pd.isna(value):
        return value

    text = str(value).strip()
    if text in ("", "."):
        return value

    try:
        number = Decimal(text)
    except InvalidOperation:
        raise ValueError("The count must be a non-negative integer or a missing value.") from None

    if not number.is_finite() or number < 0 or number != number.to_integral_value():
        raise ValueError("The count must be a non-negative integer or a missing value.")

    count = int(number)
    if count == 0:
        return 0
    if count <= SUPPRESSION_THRESHOLD:
        return REDACTED

    # Rounding integers to the nearest 5
    return ((count + ROUNDING_BASE // 2) // ROUNDING_BASE) * ROUNDING_BASE


def prepare_release(input_file, count_columns, group_columns):
    """Read a raw table, validate its structure, and return the processed table."""
    raw_df = pd.read_csv(input_file, dtype=str, keep_default_na=False)

    expected = set(count_columns) | set(group_columns)
    missing = expected - set(raw_df.columns)
    extra = set(raw_df.columns) - expected
    if missing or extra:
        raise ValueError(
            f"{input_file.name}: The column structure does not match the current Stata output. "
            f"Missing columns={sorted(missing)}；Extra columns={sorted(extra)}。"
        )

    release_df = raw_df.copy()
    for column in count_columns:
        try:
            release_df[column] = raw_df[column].map(suppress_count)
        except ValueError:
            raise ValueError(
                f"{input_file.name}: {column} Contains an invalid count"
                "Please check whether this column contains only non-negative integers or missing values."
            ) from None

    return release_df


def process_tables(input_dir, output_dir):
    """Validate all 21 tables; report error if any files are missing or mismatch structure"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    missing_files = [name for name in TABLES if not (input_dir / name).is_file()]
    if missing_files:
        raise FileNotFoundError("Missing files: " + ", ".join(missing_files))

    prepared = []
    for filename, (count_columns, group_columns) in TABLES.items():
        release_df = prepare_release(
            input_dir / filename, count_columns, group_columns,
        )
        output_file = output_dir / (Path(filename).stem + "_release.csv")
        prepared.append((output_file, release_df))

    output_dir.mkdir(parents=True, exist_ok=True)
    for output_file, release_df in prepared:
        release_df.to_csv(output_file, index=False)
        print(f"Saved: {output_file}")

    print(f"Completed: {len(prepared)} CSV files.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path("output"))
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    args = parser.parse_args()
    process_tables(args.input_dir, args.output_dir)


if __name__ == "__main__":
    main()
