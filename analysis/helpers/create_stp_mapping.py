import pandas as pd
from pathlib import Path

MAPPING_FILE = Path(__file__).resolve().parent / "categorical_mapping.csv"

mapping_df = pd.read_csv(
    MAPPING_FILE,
    dtype={"original_value": str},
    keep_default_na=False,
)

stp_mapping = pd.DataFrame([
    {
        "variable": "stp",
        "original_value": f"E540000{i:02d}",
        "encoded_value": i if i != 0 else 100,
    }
    for i in range(100)
])

stp_missing = pd.DataFrame([
    {
        "variable": "stp",
        "original_value": "Missing",
        "encoded_value": 0,
    }
])

# Remove existing STP mappings, if any
mapping_df = mapping_df.loc[
    mapping_df["variable"] != "stp"
]

mapping_df = pd.concat(
    [mapping_df, stp_missing, stp_mapping],
    ignore_index=True,
)

mapping_df.to_csv(MAPPING_FILE, index=False)