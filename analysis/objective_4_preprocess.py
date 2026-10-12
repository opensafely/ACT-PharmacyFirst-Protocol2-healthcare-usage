import pandas as pd

"""
This script preprocesses patient-month level data by selecting variables needed
for objective 4 and retaining only rows with at least one A&E attendance for
any reason, reducing the file size.
"""


INPUT_FILE = "output/dataset_patients_combined.csv"
OUTPUT_FILE = "output/dataset_patients_combined_obj4.csv"

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
    "has_ae_lbp_non_primary"
]

COLUMNS_TO_KEEP = [
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
    "inc_pt_otitis_media",
    "inc_pt_sinusitis",
    "inc_pt_sore_throat",
    "inc_pt_insect_bites",
    "inc_pt_shingles",
    "inc_pt_impetigo",
    "inc_pt_uuti",
    "inc_pt_all_eligible",
] + AE_PRIMARY_COLUMNS + AE_NON_PRIMARY_COLUMNS

CHUNK_SIZE = 200_000
row_count = 0

with open(OUTPUT_FILE, "w", newline="") as output_file:
    write_header = True

    for chunk in pd.read_csv(
        INPUT_FILE,
        usecols=COLUMNS_TO_KEEP,
        chunksize=CHUNK_SIZE,
    ):
        chunk = chunk[COLUMNS_TO_KEEP]

        # Retain only rows with at least one A&E attendance for any reason
        chunk = chunk.loc[chunk["ae_attendance_count"].fillna(0).gt(0)]

        row_count += len(chunk)

        chunk.to_csv(
            output_file,
            index=False,
            header=write_header,
        )

        write_header = False


print(
    f"Created {OUTPUT_FILE} containing "
    f"{len(COLUMNS_TO_KEEP)} selected columns and {row_count:,} rows"
)