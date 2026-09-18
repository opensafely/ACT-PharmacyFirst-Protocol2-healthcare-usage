import pandas as pd

input_file = "output/practice_measures.csv.gz"
df = pd.read_csv(input_file)

print(df.groupby("interval_start")["practice"].nunique())

df["interval_start"] = pd.to_datetime(df["interval_start"])

pop = (
    df[df["measure"] == "appointments_scheduled"]
    .rename(columns={"denominator": "population"})
    [["practice", "stp", "region", "interval_start", "population"]]
)

appt_scheduled = (
    df[df["measure"] == "appointments_scheduled"]
    .rename(columns={"numerator": "appointments_scheduled"})
    [["practice", "stp", "region", "interval_start", "appointments_scheduled"]]
)

appt_seen = (
    df[df["measure"] == "appointments_seen"]
    .rename(columns={"numerator": "appointments_seen"})
    [["practice", "stp", "region", "interval_start", "appointments_seen"]]
)

df_wide = pop.merge(appt_scheduled,on=["practice", "stp", "region", "interval_start"],how="left")
df_wide = df_wide.merge(appt_seen,on=["practice", "stp", "region", "interval_start"],how="left")

eligibility_columns = [
    "inc_pt_otitis_media",
    "inc_pt_sinusitis",
    "inc_pt_sore_throat",
    "inc_pt_insect_bites",
    "inc_pt_shingles",
    "inc_pt_impetigo",
    "inc_pt_uuti",
    "inc_pt_all_eligible",
]

for col in eligibility_columns:
    eligible_population = (
        df[df["measure"] == col]
        .rename(columns={"numerator": col})
        [
            [
                "practice",
                "stp",
                "region",
                "interval_start",
                col,
            ]
        ]
    )

    df_wide = df_wide.merge(
        eligible_population,
        on=["practice", "stp", "region", "interval_start"],
        how="left",
    )

for col in [
    "appointments_scheduled",
    "appointments_seen",
    *eligibility_columns,
]:
    df_wide[col] = df_wide[col].fillna(0)

df_wide.to_csv("output/dataset_practices.csv.gz", index=False)