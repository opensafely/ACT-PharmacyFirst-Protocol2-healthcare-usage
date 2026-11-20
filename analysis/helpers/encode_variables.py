
"""
Helper functions for encoding categorical variables using predefined
numerical mappings.

Using a fixed mapping ensures consistent encoding across datasets,
chunks, and analysis scripts.
"""

import pandas as pd
from pathlib import Path
from functools import lru_cache

DEFAULT_MAPPING_FILE = Path(__file__).resolve().parent / "categorical_mapping.csv"

@lru_cache(maxsize=None)
def load_encoding_mapping(mapping_file=DEFAULT_MAPPING_FILE):
    """
    Load categorical variable mappings from a CSV file.

    The CSV must contain the following columns:
        variable, original_value, encoded_value

    Returns
    -------
    dict
        Nested dictionary of mappings for each variable.
    """
    mapping_df = pd.read_csv(
        mapping_file,
        dtype={"variable": str, "original_value": str},
        keep_default_na=False,
    )

    required_columns = {
        "variable",
        "original_value",
        "encoded_value",
    }

    if not required_columns.issubset(mapping_df.columns):
        raise ValueError(
            "Mapping file must contain: "
            "variable, original_value, encoded_value"
        )

    mapping_df["encoded_value"] = pd.to_numeric(
        mapping_df["encoded_value"],
        errors="raise",
    ).astype("Int64")

    # Check for duplicated original values within each variable
    if mapping_df.duplicated(
        subset=["variable", "original_value"]
    ).any():
        raise ValueError(
            "Duplicate original values found in mapping file."
        )

    # Check that each encoded value has a unique original value
    if mapping_df.duplicated(
        subset=["variable", "encoded_value"]
    ).any():
        raise ValueError(
            "Duplicate encoded values found in mapping file."
        )

    return {
        variable: dict(
            zip(group["original_value"], group["encoded_value"])
        )
        for variable, group in mapping_df.groupby("variable")
    }


def encode_variables(
    df,
    mappings=None,
    columns=None,
    overwrite=True,
    suffix="_num",
):
    """
    Encode categorical variables using predefined numerical mappings.

    Parameters
    ----------
    df : pandas.DataFrame
        Input dataframe.
    mappings : dict
        Nested dictionary containing variable-specific mappings.
    columns : list, optional
        Variables to encode. If None, encode all variables in mappings.
    overwrite : bool, default True
        Whether to overwrite the original columns.
    suffix : str, default "_num"
        Suffix for encoded columns when overwrite=False.

    Returns
    -------
    pandas.DataFrame
        Dataframe containing encoded variables.

    Notes
    -----
    Missing values are preserved.
    Unmapped non-missing values raise an error.
    """
    if mappings is None:
        mappings = load_encoding_mapping()
        
    df = df.copy()

    if columns is None:
        columns = list(mappings.keys())

    for column in columns:

        if column not in df.columns:
            raise ValueError(
                f"Column '{column}' not found in dataframe."
            )

        if column not in mappings:
            raise ValueError(
                f"No encoding mapping defined for '{column}'."
            )

        values = df[column].astype("string")

        # Check for values not covered by the mapping
        unmapped = (
            values.notna()
            & ~values.isin(mappings[column].keys())
        )

        if unmapped.any():
            raise ValueError(
                f"Unmapped values found in column '{column}'. "
                "Please check the encoding mapping."
            )

        # Apply numerical encoding
        encoded = values.map(
            mappings[column]
        ).astype("Int64")

        output_column = (
            column if overwrite else f"{column}{suffix}"
        )

        if not overwrite and output_column in df.columns:
            raise ValueError(
                f"Column '{output_column}' already exists."
            )

        df[output_column] = encoded

    return df
