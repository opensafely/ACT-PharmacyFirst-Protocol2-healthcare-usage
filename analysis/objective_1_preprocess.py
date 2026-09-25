import pandas as pd


INPUT_FILE = "output/dataset_patients_combined.csv"
OUTPUT_FILE = "output/dataset_patients_combined_obj1.csv"

COLUMNS_TO_KEEP = [
    "start_date",
    "index_date",
    "practice",
    "region",
    "stp",
    "age",
    "sex",
    "ethnicity",
    "imd",
    "pf_cons_general",
    "num_pf_cons_uti",
    "num_pf_cons_sinusitis",
    "num_pf_cons_ibite",
    "num_pf_cons_otitismedia",
    "num_pf_cons_sorethroat",
    "num_pf_cons_shingles",
    "num_pf_cons_impetigo",
    "inc_pt_otitis_media",
    "inc_pt_sinusitis",
    "inc_pt_sore_throat",
    "inc_pt_insect_bites",
    "inc_pt_shingles",
    "inc_pt_impetigo",
    "inc_pt_uuti",
    "inc_pt_all_eligible",
]

CHUNK_SIZE = 200_000

with open(OUTPUT_FILE, "w", newline="") as output_file:
    write_header = True

    for chunk in pd.read_csv(
        INPUT_FILE,
        usecols=COLUMNS_TO_KEEP,
        chunksize=CHUNK_SIZE,
    ):
        chunk = chunk[COLUMNS_TO_KEEP]

        # Retain only rows with at least one PF consultation
        chunk = chunk.loc[chunk["pf_cons_general"].fillna(0).gt(0)]

        chunk.to_csv(
            output_file,
            index=False,
            header=write_header,
        )

        write_header = False


print(
    f"Created {OUTPUT_FILE} containing "
    f"{len(COLUMNS_TO_KEEP)} selected columns"
)