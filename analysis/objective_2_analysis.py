"""
Objective 2 (descriptive): Evaluate any change in overall General Practice (GP) consultations by examining the trend over time

This script generates unsuppressed practice-month and monthly overall appointment tables.
"""

from pathlib import Path
import pandas as pd

# Input and output file path
INPUT_FILE = "output/dataset_patients_combined.csv" # Input: patient X month
PRACTICE_OUTPUT_FILE = "output/appointment_practice_month.csv" # practice X month
MONTHLY_OUTPUT_FILE = "output/appointment_monthly_overall.csv" # monthly overall - small practices (patient count < 500) are excluded from all counts

# Input column names
MONTH_COLUMN = "start_date"
PRACTICE_COLUMN = "practice"
SEEN_COLUMN = "appointment_seen"
SCHEDULED_COLUMN = "appointment_scheduled"
CHUNK_SIZE = 250_000

# Key column names
COUNTS = ["patient_count", "appointment_seen_count", "appointment_scheduled_count"]
PRACTICE_COLUMNS = ["month", "practice_id", *COUNTS,
                    "appointment_seen_rate", "appointment_scheduled_rate",
                    "small_practice_flag"]
MONTHLY_COLUMNS = ["month", "patient_count", "eligible_practice_count",
                   "appointment_seen_count", "appointment_scheduled_count",
                   "appointment_seen_rate", "appointment_scheduled_rate"]


def add_rates(table):
    denominator = table["patient_count"].where(table["patient_count"] > 0)
    for kind in ("seen", "scheduled"):
        table[f"appointment_{kind}_rate"] = table[f"appointment_{kind}_count"] * 1000.0 / denominator
    return table


def build_tables(input_file, 
                 month_col="month", 
                 practice_col="practice_id",
                 seen_col="appointment_seen", 
                 scheduled_col="appointment_scheduled",
                 chunksize=250_000):
    source_cols = [month_col, practice_col, seen_col, scheduled_col]
    if len(set(source_cols)) != 4:
        raise ValueError("The four input column names must be distinct.")
    if chunksize < 1:
        raise ValueError("chunksize must be positive.")
    header = pd.read_csv(input_file, nrows=0)
    missing = sorted(set(source_cols) - set(header.columns))
    if missing:
        raise ValueError(f"Missing input columns: {missing}. Update the input column constants at the top of the script.")

    totals = None
    rows_read = 0
    # Keep identifiers as strings to avoid losing leading zeroes or precision.
    # Do not interpret literal identifiers such as 'NA' as missing values.
    reader = pd.read_csv(input_file, usecols=source_cols, dtype="string",
                         keep_default_na=False, chunksize=chunksize)
    for chunk in reader:
        if chunk.empty:
            continue
        chunk = chunk.rename(columns=dict(zip(
            source_cols, ["month", "practice_id", "seen", "scheduled"])))
        for name in ("month", "practice_id"):
            chunk[name] = chunk[name].str.strip()
            if chunk[name].eq("").any():
                raise ValueError(f"Missing {name}; no records have been dropped.")

        # Accept only explicit ISO month/date representations; do not guess dates.
        valid = chunk["month"].str.fullmatch(r"\d{4}-\d{2}(-\d{2})?")
        if not valid.all():
            raise ValueError("Month must be YYYY-MM or YYYY-MM-DD.")
        dates = chunk["month"].where(chunk["month"].str.len() == 10,
                                     chunk["month"] + "-01")
        chunk["month"] = pd.to_datetime(
            dates, format="%Y-%m-%d", errors="raise").dt.strftime("%Y-%m")

        for name in ("seen", "scheduled"):
            # Missing counts are errors, not silently converted to zero.
            values = pd.to_numeric(chunk[name], errors="raise")
            if (values.isna().any() or (values < 0).any()
                    or (values % 1 != 0).any() or (values > 2**63 - 1).any()):
                raise ValueError(f"{name} must contain non-negative integer counts.")
            chunk[name] = values.astype("int64")

        chunk["patient_count"] = 1
        chunk = chunk.rename(columns={"seen": "appointment_seen_count",
                                      "scheduled": "appointment_scheduled_count"})
        grouped = chunk.groupby(["month", "practice_id"], sort=False)[COUNTS].sum()
        # Aggregate across chunk boundaries before applying the 500-patient rule.
        if totals is None:
            totals = grouped
        else:
            totals = pd.concat([totals, grouped]).groupby(level=[0, 1]).sum()
        rows_read += len(chunk)

    if totals is None:
        return (pd.DataFrame(columns=PRACTICE_COLUMNS),
                pd.DataFrame(columns=MONTHLY_COLUMNS), rows_read)

    practice = totals.reset_index().sort_values(["month", "practice_id"])
    practice["small_practice_flag"] = practice["patient_count"] < 500
    practice = add_rates(practice)

    included = practice.loc[~practice["small_practice_flag"]]
    monthly = included.groupby("month")[COUNTS].sum()
    monthly["eligible_practice_count"] = included.groupby("month")["practice_id"].nunique()
    # Retain months in which every observed practice is excluded: zero counts,
    # zero practices, and missing rates (there is no eligible denominator).
    months = pd.Index(sorted(practice["month"].unique()), name="month")
    monthly = monthly.reindex(months, fill_value=0).reset_index()
    monthly[COUNTS + ["eligible_practice_count"]] = monthly[COUNTS + ["eligible_practice_count"]].astype("int64")
    monthly = add_rates(monthly)
    return practice[PRACTICE_COLUMNS], monthly[MONTHLY_COLUMNS], rows_read


def main():
    paths = [Path(p).resolve() for p in (INPUT_FILE, PRACTICE_OUTPUT_FILE, MONTHLY_OUTPUT_FILE)]
    if len(set(paths)) != 3:
        raise ValueError("Input and both output paths must be distinct.")
    practice, monthly, rows_read = build_tables(
        INPUT_FILE, MONTH_COLUMN, PRACTICE_COLUMN,
        SEEN_COLUMN, SCHEDULED_COLUMN, CHUNK_SIZE)
    for table, output in ((practice, PRACTICE_OUTPUT_FILE),
                          (monthly, MONTHLY_OUTPUT_FILE)):
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(output, index=False, na_rep="")
    print(f"Processed {rows_read} eligible patient-month rows.")
    print(f"Practice-month table: {len(practice)} rows -> {PRACTICE_OUTPUT_FILE}")
    print(f"Monthly overall table: {len(monthly)} rows -> {MONTHLY_OUTPUT_FILE}")


if __name__ == "__main__":
    main()
