"""
This script preprocesses patient-month level data by selecting variables needed
for objective 3 and retaining only rows with at least one GP consultation for
the selected PF-related conditions, reducing the file size.
"""

import pandas as pd
from pathlib import Path
from helpers.encode_variables import encode_variables

# =============================================================================
# Configuration
# =============================================================================

CHUNK_SIZE = 200_000

INPUT_FILE = "output/dataset_patients_combined.csv.gz"
OUTPUT_FILE_NUMERATOR = "output/dataset_patients_obj3_numerator.csv"

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

GP_CONS_COLUMNS = [
    "num_gp_cons_uti",
    "num_gp_cons_sinusitis",
    "num_gp_cons_ibite",
    "num_gp_cons_otitismedia",
    "num_gp_cons_sorethroat",
    "num_gp_cons_shingles",
    "num_gp_cons_impetigo",
    "num_gp_cons_ibite_strict",
    "num_gp_cons_ibite_all",
    "num_gp_cons_cellulitis_only",
    "num_gp_cons_ibite_strict_or_all",
    "num_gp_cons_ibite_all_plus_cellulitis",
    "num_gp_cons_ibite_strict_or_all_plus_cellulitis",
    "num_gp_cons_lbp",
]

NUMERATOR_COLUMNS = (
    COMMON_COLUMNS
    + ELIGIBILITY_COLUMNS
    + GP_CONS_COLUMNS
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

        # Retain only rows with at least one GP consultation
        # for the selected conditions
        numerator_chunk = chunk.loc[
            chunk[GP_CONS_COLUMNS].fillna(0).gt(0).any(axis=1),
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