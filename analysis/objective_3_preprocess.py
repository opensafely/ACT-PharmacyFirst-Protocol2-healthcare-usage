import pandas as pd

"""
This script preprocesses patient-month level data by selecting variables needed
for objective 3 and retaining only rows with at least one GP consultation for
the selected PF-related conditions, reducing the file size.
"""


INPUT_FILE = "output/dataset_patients_combined.csv"
OUTPUT_FILE = "output/dataset_patients_combined_obj3.csv"

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
] + GP_CONS_COLUMNS

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

        # Retain only rows with at least one GP consultation for selected conditions
        chunk = chunk.loc[chunk[GP_CONS_COLUMNS].fillna(0).gt(0).any(axis=1)]
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