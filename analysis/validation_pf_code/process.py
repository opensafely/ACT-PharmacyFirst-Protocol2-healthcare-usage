import os

import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = "output/patient_measures_pf_service_codes.csv"
OUTPUT_DIR = "output/pf_code_validation"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_measures(path):
    df = pd.read_csv(path)
    df["interval_start"] = pd.to_datetime(df["interval_start"])
    return df

def pivot_measures(df, measures):
    out = (
        df[df["measure"].isin(measures)]
        .pivot(index="interval_start", columns="measure", values="numerator")
        .reset_index()
        .sort_values("interval_start")
    )
    return out

def plot_monthly_counts(df, measures, title, output_file):
    plot_df = pivot_measures(df, measures)

    ax = plot_df.plot(
        x="interval_start",
        y=measures,
        figsize=(10, 6),
        marker="o",
    )

    ax.set_title(title)
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    ax.legend(title="Measure")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()


df = read_measures(INPUT_FILE)

# 1. Monthly service code consultation counts
service_consultation_measures = [
    "minor_illness_consultations",
    "pf_service_consultations",
    "pf_cp_service_consultations",
]

plot_monthly_counts(
    df,
    service_consultation_measures,
    "Monthly consultation counts by PF service code",
    os.path.join(OUTPUT_DIR, "monthly_service_code_consultations.png"),
)

pivot_measures(df, service_consultation_measures).to_csv(
    os.path.join(OUTPUT_DIR, "monthly_service_code_consultations.csv"),
    index=False,
)


# 2. Monthly service code event counts
service_event_measures = [
    "minor_illness_events",
    "pf_service_events",
    "pf_cp_service_events",
]

plot_monthly_counts(
    df,
    service_event_measures,
    "Monthly event counts by PF service code",
    os.path.join(OUTPUT_DIR, "monthly_service_code_events.png"),
)

pivot_measures(df, service_event_measures).to_csv(
    os.path.join(OUTPUT_DIR, "monthly_service_code_events.csv"),
    index=False,
)


# 3. Monthly overlap counts
overlap_measures = [
    "minorillness_and_pf_service_same_consultations",
    "minorillness_consultations_within_7days_of_pf_service_event",
    "pf_service_consultations_within_7days_of_minorillness_event",
]

plot_monthly_counts(
    df,
    overlap_measures,
    "Monthly overlap between minor illness and PF service codes",
    os.path.join(OUTPUT_DIR, "monthly_code_overlap.png"),
)

pivot_measures(df, overlap_measures).to_csv(
    os.path.join(OUTPUT_DIR, "monthly_code_overlap.csv"),
    index=False,
)


# 4. PF condition consultations by service code, shown separately by month
conditions = [
    "uti",
    "sinusitis",
    "insectbite",
    "otitismedia",
    "sorethroat",
    "shingles",
    "impetigo",
]

condition_rows = []

for condition in conditions:
    for service_label, measure_name in [
        ("combined_pf_service_codes", f"pf_consultation_{condition}"),
        ("minor_illness_code", f"minorillness_pf_consultation_{condition}"),
        ("pf_service_code", f"pfservice_pf_consultation_{condition}"),
    ]:
        condition_df = df[df["measure"] == measure_name].copy()

        for _, row in condition_df.iterrows():
            condition_rows.append(
                {
                    "interval_start": row["interval_start"],
                    "condition": condition,
                    "service_code_definition": service_label,
                    "consultations": row["numerator"],
                }
            )

condition_summary = pd.DataFrame(condition_rows)
condition_summary.to_csv(
    os.path.join(OUTPUT_DIR, "condition_consultations_by_service_code_monthly.csv"),
    index=False,
)

months_available = sorted(condition_summary["interval_start"].unique())

fig, axes = plt.subplots(
    1,
    len(months_available),
    figsize=(7 * len(months_available), 6),
    sharey=True,
)

if len(months_available) == 1:
    axes = [axes]

for ax, month in zip(axes, months_available):
    month_df = condition_summary[condition_summary["interval_start"] == month]

    plot_df = (
        month_df
        .pivot(
            index="condition",
            columns="service_code_definition",
            values="consultations",
        )
        .reindex(conditions)
    )

    plot_df.plot(kind="bar", ax=ax)

    ax.set_title(pd.to_datetime(month).strftime("%Y-%m"))
    ax.set_xlabel("PF condition")
    ax.set_ylabel("Consultation count")
    ax.grid(True, axis="y", alpha=0.3)
    ax.tick_params(axis="x", rotation=45)

# Use a single shared legend
handles, labels = axes[0].get_legend_handles_labels()
for ax in axes:
    ax.get_legend().remove()

fig.suptitle("PF condition consultations by service code definition", y=0.98)

fig.legend(
    handles,
    labels,
    title="Service code definition",
    loc="lower center",
    ncol=3,
    bbox_to_anchor=(0.5, -0.02),
)

plt.tight_layout(rect=[0, 0.08, 1, 0.94])

plt.savefig(
    os.path.join(OUTPUT_DIR, "condition_consultations_by_service_code_by_month.png"),
    dpi=300,
    bbox_inches="tight",
)
plt.close()