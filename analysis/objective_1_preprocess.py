import pandas as pd

"""
This script preprocesses patient-month level data for Objetcive 1.

It reads the compressed combined dataset in chuncks, select the required columns,
and retain only records with at least one general PF consultation.

The processed data are saved as an uncompressed CSV for downstream Stata analysis.
"""
from pathlib import Path
from helpers.encode_variables import encode_variables

# =============================================================================
# Configuration
# =============================================================================

CHUNK_SIZE = 200_000

INPUT_FILE = "output/dataset_patients_combined.csv.gz"
OUTPUT_FILE_NUMERATOR = "output/dataset_patients_obj1_numerator.csv"
OUTPUT_FILE_DENOMINATOR = "output/dataset_patients_obj1_denominator.csv"

COMMON_COLUMNS = [
    "pt_id",
    "start_date",
    "index_date",
    "practice",
    "region",
    "stp",
    "age",
    "sex",
    "ethnicity",
    "imd",
]

CONSULTATION_COLUMNS = [
    "pf_cons_general",
    "num_pf_cons_uti",
    "num_pf_cons_sinusitis",
    "num_pf_cons_ibite",
    "num_pf_cons_otitismedia",
    "num_pf_cons_sorethroat",
    "num_pf_cons_shingles",
    "num_pf_cons_impetigo",
]

ELIGIBILITY_COLUMNS = [
    "inc_pt_otitis_media",
    "inc_pt_sinusitis",
    "inc_pt_sore_throat",
    "inc_pt_insect_bites",
    "inc_pt_shingles",
    "inc_pt_impetigo",
    "inc_pt_uuti",
    "inc_pt_all_eligible",
]

NUMERATOR_COLUMNS = (
    COMMON_COLUMNS
    + CONSULTATION_COLUMNS
    + ELIGIBILITY_COLUMNS
)

DENOMINATOR_COLUMNS = (
    COMMON_COLUMNS
    + ELIGIBILITY_COLUMNS
)

COLUMNS_TO_ENCODE = [
    "region",
    "stp",
    "sex",
    "ethnicity",
    "imd",
]

# =============================================================================
# Read and process the combined dataset in chunks
# =============================================================================

numerator_rows = 0
denominator_rows = 0

with (
    open(OUTPUT_FILE_NUMERATOR, "w", newline="") as numerator_file,
    open(OUTPUT_FILE_DENOMINATOR, "w", newline="") as denominator_file,
):
    write_header = True

    for chunk in pd.read_csv(
        INPUT_FILE,
        usecols=NUMERATOR_COLUMNS,
        chunksize=CHUNK_SIZE,
    ):

        # Encode categorical variables once for both datasets
        chunk = encode_variables(
            chunk,
            columns=COLUMNS_TO_ENCODE,
        )

        # ---------------------------------------------------------------------
        # Numerator dataset
        # ---------------------------------------------------------------------

        # Retain only rows with at least one PF consultation
        numerator_chunk = chunk.loc[
            chunk["pf_cons_general"].fillna(0).gt(0),
            NUMERATOR_COLUMNS,
        ]

        numerator_chunk.to_csv(
            numerator_file,
            index=False,
            header=write_header,
        )

        numerator_rows += len(numerator_chunk)

        # ---------------------------------------------------------------------
        # Denominator dataset
        # ---------------------------------------------------------------------

        # Retain all rows and select denominator columns
        denominator_chunk = chunk[DENOMINATOR_COLUMNS]

        denominator_chunk.to_csv(
            denominator_file,
            index=False,
            header=write_header,
        )

        denominator_rows += len(denominator_chunk)

        write_header = False


# =============================================================================
# Report processing results
# =============================================================================

print(
    f"Created {OUTPUT_FILE_NUMERATOR} containing "
    f"{numerator_rows:,} rows and "
    f"{len(NUMERATOR_COLUMNS)} selected columns"
)

print(
    f"Created {OUTPUT_FILE_DENOMINATOR} containing "
    f"{denominator_rows:,} rows and "
    f"{len(DENOMINATOR_COLUMNS)} selected columns"
)

for output_file in [
    OUTPUT_FILE_NUMERATOR,
    OUTPUT_FILE_DENOMINATOR,
]:
    size_bytes = Path(output_file).stat().st_size
    size_mb = size_bytes / 1024**2
    size_gb = size_bytes / 1024**3

    print(
        f"File size of {output_file}: "
        f"{size_mb:,.2f} MB ({size_gb:,.2f} GB)"
    )