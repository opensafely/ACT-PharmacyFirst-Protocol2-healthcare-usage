
"""
This script preprocesses patient-month level data for Objective 4.

It reads the compressed combined dataset in chunks, selects the required
columns, and retains only records with at least one A&E attendance for
any reason.

Categorical variables are encoded using predefined mappings to reduce
the file size and memory usage in downstream Stata analysis.

The numerator dataset is saved as an uncompressed CSV.
"""

from pathlib import Path
import pandas as pd

from helpers.encode_variables import encode_variables

# =============================================================================
# Configuration
# =============================================================================

CHUNK_SIZE = 200_000

INPUT_FILE = "output/dataset_patients_combined.csv.gz"
OUTPUT_FILE_NUMERATOR = "output/dataset_patients_obj4_numerator.csv"

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

AE_PRIMARY_COLUMNS = [
    "ae_attendance_count",
    "ae_uti_primary_count",
    "ae_sinusitis_primary_count",
    "ae_ibite_primary_count",
    "ae_otitismedia_primary_count",
    "ae_sorethroat_primary_count",
    "ae_shingles_primary_count",
    "ae_impetigo_primary_count",
    "ae_ibite_strict_primary_count",
    "ae_ibite_all_primary_count",
    "ae_cellulitis_only_primary_count",
    "ae_ibite_strict_or_all_primary_count",
    "ae_lbp_primary_count",
]

AE_NON_PRIMARY_COLUMNS = [
    "has_ae_uti_non_primary",
    "has_ae_sinusitis_non_primary",
    "has_ae_ibite_non_primary",
    "has_ae_otitismedia_non_primary",
    "has_ae_sorethroat_non_primary",
    "has_ae_shingles_non_primary",
    "has_ae_impetigo_non_primary",
    "has_ae_ibite_strict_non_primary",
    "has_ae_ibite_all_non_primary",
    "has_ae_cellulitis_only_non_primary",
    "has_ae_ibite_strict_or_all_non_primary",
    "has_ae_lbp_non_primary",
]

NUMERATOR_COLUMNS = (
    COMMON_COLUMNS
    + ELIGIBILITY_COLUMNS
    + AE_PRIMARY_COLUMNS
    + AE_NON_PRIMARY_COLUMNS
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

with open(OUTPUT_FILE_NUMERATOR, "w", newline="") as numerator_file:
    write_header = True

    for chunk in pd.read_csv(
        INPUT_FILE,
        usecols=NUMERATOR_COLUMNS,
        chunksize=CHUNK_SIZE,
    ):

        # Retain only rows with at least one A&E attendance
        # for any reason
        numerator_chunk = chunk.loc[
            chunk["ae_attendance_count"].fillna(0).gt(0),
            NUMERATOR_COLUMNS,
        ]

        # Encode categorical variables
        numerator_chunk = encode_variables(
            numerator_chunk,
            columns=COLUMNS_TO_ENCODE,
        )

        # Save the numerator dataset
        numerator_chunk.to_csv(
            numerator_file,
            index=False,
            header=write_header,
        )

        numerator_rows += len(numerator_chunk)
        write_header = False


# =============================================================================
# Report processing results
# =============================================================================

print(
    f"Created {OUTPUT_FILE_NUMERATOR} containing "
    f"{numerator_rows:,} rows and "
    f"{len(NUMERATOR_COLUMNS)} selected columns"
)

# Report output file size
size_bytes = Path(OUTPUT_FILE_NUMERATOR).stat().st_size
size_mb = size_bytes / 1024**2
size_gb = size_bytes / 1024**3

print(
    f"File size of {OUTPUT_FILE_NUMERATOR}: "
    f"{size_mb:,.2f} MiB ({size_gb:,.2f} GiB)"
)
