from pathlib import Path

import pandas as pd


INPUT_FILE = "output/dataset_patients_combined_obj1.csv"
CHUNK_SIZE = 200_000


input_path = Path(INPUT_FILE)

number_of_rows = 0
number_of_columns = 0

for chunk_number, chunk in enumerate(
    pd.read_csv(
        input_path,
        chunksize=CHUNK_SIZE,
    )
):
    number_of_rows += len(chunk)

    if chunk_number == 0:
        number_of_columns = len(chunk.columns)


file_size_gb = input_path.stat().st_size / 1_000_000_000


results = (
    f"File: {INPUT_FILE}\n"
    f"Rows: {number_of_rows:,}\n"
    f"Columns: {number_of_columns:,}\n"
    f"File size: {file_size_gb:.3f} GB\n"
)

print(results)

with open("output/objective_1_file_checks.txt", "w") as output_file:
    output_file.write(results)