
import argparse
from pathlib import Path

import pandas as pd

"""
Generate denominator tables for Objective 1.

Read the combined patient-month dataset in chunks and aggregate
condition-specific and overall eligible patient counts.

Generate 8 one-way, 7 two-way and 6 three-way denominator tables
corresponding to the existing numerator outputs.

No rounding or suppression is applied.
"""

INPUT_FILE = "output/dataset_patients_combined.csv.gz"
OUTPUT_DIR = Path("output")
CHUNK_SIZE = 200_000

# Map eligibility variables to the condition names used in the numerator tables.
ELIGIBILITY_COLUMNS = {
    "inc_pt_all_eligible": "sumall",
    "inc_pt_insect_bites": "sumibite",
    "inc_pt_impetigo": "sumimpetigo",
    "inc_pt_otitis_media": "sumotitismedia",
    "inc_pt_shingles": "sumshingles",
    "inc_pt_sinusitis": "sumsinusitis",
    "inc_pt_sore_throat": "sumsorethroat",
    "inc_pt_uuti": "sumuti",
}

DENOM_COLUMNS = list(ELIGIBILITY_COLUMNS.values())

SUBGROUPS = [
    "region",
    "stp",
    "age_group",
    "sex",
    "ethnicity",
    "imd",
]

COLUMNS_TO_KEEP = [
    "index_date",
    "age",
    "region",
    "stp",
    "sex",
    "ethnicity",
    "imd",
    *ELIGIBILITY_COLUMNS.keys(),
]


def preprocess_chunk(chunk, start_date=None):
    """Prepare dates, age groups and eligibility indicators."""

    # Convert index date
    chunk["index_date"] = pd.to_datetime(
        chunk["index_date"],
        format="%Y-%m-%d",
        errors="raise",
    )

    if chunk["index_date"].isna().any():
        raise ValueError("Missing index_date values found.")

    # Optional restriction of analysis period
    if start_date is not None:
        chunk = chunk.loc[
            chunk["index_date"] >= start_date
        ].copy()

    # Create age groups consistent with numerator analysis
    age = pd.to_numeric(chunk["age"], errors="raise")

    chunk["age_group"] = pd.cut(
        age,
        bins=[0, 20, 40, 60, 80, float("inf")],
        labels=[
            "0_to_19",
            "20_to_39",
            "40_to_59",
            "60_to_79",
            "80_and_over",
        ],
        right=False,
    ).astype("string")

    # Retain missing subgroup values during aggregation
    for subgroup in SUBGROUPS:
        chunk[subgroup] = (
            chunk[subgroup]
            .astype("string")
            .fillna("")
        )

    # Convert eligibility indicators to integers
    for column in ELIGIBILITY_COLUMNS:
        values = (
            chunk[column]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        converted = values.map({
            "T": 1,
            "F": 0,
            "TRUE": 1,
            "FALSE": 0,
            "1": 1,
            "0": 0,
        })

        # Check for unexpected non-missing values
        invalid = values.notna() & converted.isna()

        if invalid.any():
            raise ValueError(
                f"Unexpected eligibility values in {column}: "
                f"{values[invalid].unique().tolist()}"
            )

        chunk[column] = converted.fillna(0).astype("int64")

    # Rename to match numerator output columns
    chunk = chunk.rename(columns=ELIGIBILITY_COLUMNS)

    return chunk


def aggregate(df, group_columns):
    """Sum eligibility counts by the specified grouping variables."""

    return (
        df.groupby(
            group_columns,
            dropna=False,
            observed=True,
        )[DENOM_COLUMNS]
        .sum()
        .reset_index()
    )


def combine_aggregates(existing, new, group_columns):
    """Combine an aggregated chunk with accumulated results."""

    if existing is None:
        return new

    combined = pd.concat(
        [existing, new],
        ignore_index=True,
    )

    return aggregate(combined, group_columns)


def process_dataset(input_file, chunksize, start_date=None):
    """
    Read the patient-month dataset once.

    Calculate:
        - date-level denominator counts
        - date x subgroup denominator counts
          for each of the six subgroups
    """

    groupings = {
        "date": ["index_date"],
        **{
            subgroup: ["index_date", subgroup]
            for subgroup in SUBGROUPS
        },
    }

    results = {
        name: None
        for name in groupings
    }

    total_rows_read = 0
    total_rows_included = 0

    for i, chunk in enumerate(
        pd.read_csv(
            input_file,
            usecols=COLUMNS_TO_KEEP,
            chunksize=chunksize,
            dtype={
                **{
                    column: "string"
                    for column in ELIGIBILITY_COLUMNS
                },
                "region": "string",
                "stp": "string",
                "sex": "string",
                "ethnicity": "string",
                "imd": "string",
            },
        ),
        start=1,
    ):
        total_rows_read += len(chunk)

        chunk = preprocess_chunk(
            chunk,
            start_date=start_date,
        )

        total_rows_included += len(chunk)

        if chunk.empty:
            continue

        for name, group_columns in groupings.items():
            chunk_aggregated = aggregate(
                chunk,
                group_columns,
            )

            results[name] = combine_aggregates(
                results[name],
                chunk_aggregated,
                group_columns,
            )

        print(
            f"Processed chunk {i:,} | "
            f"Rows read: {total_rows_read:,} | "
            f"Rows included: {total_rows_included:,}",
            flush=True,
        )

    if total_rows_included == 0:
        raise ValueError("No patient-month records included.")

    print(
        f"Total rows read: {total_rows_read:,}",
        flush=True,
    )

    print(
        f"Total rows included: {total_rows_included:,}",
        flush=True,
    )

    return results


def format_date(df):
    """Format date consistently with the numerator tables."""

    df = df.copy()

    df["date"] = df["index_date"].dt.strftime("%Y/%m/%d")
    df = df.drop(columns="index_date")

    # Place date as the first column
    columns = [
        "date",
        *[col for col in df.columns if col != "date"],
    ]

    return df[columns]


def export_table(df, filename):
    """Save a denominator table."""

    output_file = OUTPUT_DIR / filename

    df.to_csv(
        output_file,
        index=False,
    )

    print(
        f"Created {output_file} ({len(df):,} rows)",
        flush=True,
    )


def generate_oneway_tables(results):
    """Generate the eight one-way denominator tables."""

    # --------------------------------------------------
    # Condition
    # --------------------------------------------------

    condition_totals = (
        results["date"][DENOM_COLUMNS]
        .sum()
        .reset_index()
    )

    condition_totals.columns = ["condition", "sum"]

    condition_totals["condition"] = (
        condition_totals["condition"].str.slice(3)
    )

    condition_totals = condition_totals.sort_values(
        "condition"
    )

    export_table(
        condition_totals,
        "oneway_date_condition_denom.csv",
    )

    # --------------------------------------------------
    # Date
    # --------------------------------------------------

    date_totals = results["date"][
        ["index_date", "sumall"]
    ].copy()

    date_totals = date_totals.rename(
        columns={"sumall": "sum"}
    )

    date_totals = format_date(date_totals)

    export_table(
        date_totals,
        "oneway_date_denom.csv",
    )

    # --------------------------------------------------
    # Patient characteristics
    # --------------------------------------------------

    for subgroup in SUBGROUPS:
        subgroup_totals = aggregate(
            results[subgroup],
            [subgroup],
        )

        subgroup_totals = subgroup_totals[
            [subgroup, "sumall"]
        ].rename(
            columns={"sumall": "sum"}
        )

        export_table(
            subgroup_totals,
            f"oneway_{subgroup}_denom.csv",
        )


def generate_twoway_tables(results):
    """Generate the seven two-way denominator tables."""

    # --------------------------------------------------
    # Date x condition
    # --------------------------------------------------

    date_condition = format_date(results["date"])

    export_table(
        date_condition,
        "twoway_date_condition_denom.csv",
    )

    # --------------------------------------------------
    # Subgroup x condition
    # --------------------------------------------------

    for subgroup in SUBGROUPS:
        subgroup_condition = aggregate(
            results[subgroup],
            [subgroup],
        )

        export_table(
            subgroup_condition,
            f"twoway_{subgroup}_condition_denom.csv",
        )


def generate_threeway_tables(results):
    """Generate the six three-way denominator tables."""

    for subgroup in SUBGROUPS:
        df = results[subgroup].copy()

        # Match the subgroup labels used in the
        # corresponding numerator three-way tables.
        if subgroup == "region":
            df["region"] = df["region"].replace({
                "North East": "North_East",
                "North West": "North_West",
                "South East": "South _East",
                "South West": "South _West",
                "West Midlands": "West_Midlands",
                "Yorkshire and The Humber":
                    "Yorkshire_and_The_Humber",
            })

            df = df.rename(
                columns={"region": "region_num"}
            )

        elif subgroup == "ethnicity":
            df["ethnicity"] = (
                df["ethnicity"]
                .str.replace(" ", "_", regex=False)
            )

        elif subgroup == "imd":
            df["imd"] = df["imd"].replace({
                "5 (Least Deprived)": "5",
            })

        # Combine any groups that now share the same label
        output_subgroup = (
            "region_num" if subgroup == "region"
            else subgroup
        )

        df = aggregate(
            df,
            ["index_date", output_subgroup],
        )

        df = format_date(df)

        export_table(
            df,
            f"threeway_condition_date_{subgroup}_denom.csv",
        )


def validate_results(results):
    """
    Check that subgroup-level denominator counts reconcile
    with date-level denominator counts before rounding.
    """

    expected = (
        results["date"]
        .set_index("index_date")[DENOM_COLUMNS]
        .sort_index()
    )

    for subgroup in SUBGROUPS:
        observed = (
            aggregate(
                results[subgroup],
                ["index_date"],
            )
            .set_index("index_date")[DENOM_COLUMNS]
            .sort_index()
        )

        pd.testing.assert_frame_equal(
            expected,
            observed,
            check_dtype=False,
        )

        print(
            f"Validation passed: {subgroup}",
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        default=INPUT_FILE,
        help="Input patient-month dataset",
    )

    parser.add_argument(
        "--chunksize",
        type=int,
        default=CHUNK_SIZE,
        help="Number of rows to process per chunk",
    )

    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional analysis start date (YYYY-MM-DD)",
    )

    args = parser.parse_args()

    start_date = (
        pd.Timestamp(args.start_date)
        if args.start_date is not None
        else None
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = process_dataset(
        input_file=args.input,
        chunksize=args.chunksize,
        start_date=start_date,
    )

    # Validate aggregated counts before exporting
    validate_results(results)

    generate_oneway_tables(results)
    generate_twoway_tables(results)
    generate_threeway_tables(results)

    print(
        "Completed: 21 denominator tables generated.",
        flush=True,
    )


if __name__ == "__main__":
    main()
