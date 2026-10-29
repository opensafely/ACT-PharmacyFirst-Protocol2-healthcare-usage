"""Plot monthly overall GP appointment counts and rates using seaborn.

Input is the monthly overall table restricted to eligible practices.
No suppression or rounding is performed here: the plots inherit the disclosure
status of the input. Missing values are shown as gaps, not filled or interpolated.
Run from the project root. Requires pandas, matplotlib and seaborn.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Save figures without a display (OpenSAFELY actions).

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


INPUT_FILE = "output/appointment_monthly_overall.csv"
COUNT_OUTPUT_FILE = "output/appointment_monthly_counts_trend.png"
RATE_OUTPUT_FILE = "output/appointment_monthly_rates_trend.png"

# Use the same labels and colours in both figures.
COLOURS = {"Seen": "#0072B2", "Scheduled": "#D55E00"}
FIGURE_SIZE = (14, 6)
DPI = 300


def load_data():
    columns = [
        "month",
        "appointment_seen_count",
        "appointment_scheduled_count",
        "appointment_seen_rate",
        "appointment_scheduled_rate",
    ]
    data = pd.read_csv(INPUT_FILE, dtype={"month": "string"})
    missing = sorted(set(columns) - set(data.columns))
    if missing:
        raise ValueError(f"Missing input columns: {missing}")
    if data.empty:
        raise ValueError("The monthly overall CSV contains no data rows.")

    month = data["month"].str.strip()
    if not month.str.fullmatch(r"\d{4}-\d{2}(-\d{2})?").fillna(False).all():
        raise ValueError("month must contain YYYY-MM or YYYY-MM-DD values.")
    dates = month.where(month.str.len() == 10, month + "-01")
    data["month"] = pd.to_datetime(dates, format="%Y-%m-%d", errors="raise")
    data["month"] = data["month"].dt.to_period("M").dt.to_timestamp()
    if data["month"].duplicated().any():
        raise ValueError("Expected exactly one row per calendar month.")

    for column in columns[1:]:
        data[column] = pd.to_numeric(data[column], errors="raise")
        if (data[column].dropna() < 0).any() or data[column].isin([float("inf"), -float("inf")]).any():
            raise ValueError(f"{column} must contain finite, non-negative values or blanks.")

    data = data[columns].sort_values("month").set_index("month")
    # Add absent months as missing values, so lines do not bridge missing months.
    months = pd.date_range(data.index.min(), data.index.max(), freq="MS", name="month")
    return data.reindex(months).reset_index()


def plot_trend(data, seen_column, scheduled_column, title, subtitle, ylabel, output_file):
    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    for label, column in (("Seen", seen_column), ("Scheduled", scheduled_column)):
        # Draw separate continuous segments: seaborn otherwise drops missing
        # values and may connect points across gaps.
        valid = data[column].notna()
        segments = valid.ne(valid.shift(fill_value=False)).cumsum()
        for _, segment in data.loc[valid].groupby(segments[valid]):
            sns.lineplot(
                data=segment,
                x="month",
                y=column,
                color=COLOURS[label],
                marker="o",
                markersize=4,
                linewidth=1.8,
                estimator=None,
                legend=False,
                ax=ax,
            )
        # Explicit legend handles keep colours/order stable, even for empty series.
        ax.plot([], [], color=COLOURS[label], marker="o", linewidth=1.8, label=label)

    ax.set(xlabel="Month", ylabel=ylabel)
    # Main title
    ax.set_title(title, fontsize=14, pad=32)
    # Subtitle
    ax.text(
        0.5,
        1.02,
        subtitle,
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=10,
        color="dimgray",
    )

    ax.set_ylim(bottom=0)
    locator = mdates.AutoDateLocator(minticks=4, maxticks=10, interval_multiples=True)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.tick_params(axis="x", labelrotation=30)
    for tick in ax.get_xticklabels():
        tick.set_horizontalalignment("right")
    ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    ax.legend(title="Appointment", frameon=False)
    sns.despine(ax=ax)
    fig.tight_layout()
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_file, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {output_file}")


def main():
    sns.set_theme(style="whitegrid", context="notebook", rc={"grid.linestyle": "--", "grid.alpha": 0.5},)
    data = load_data()
    plot_trend(
        data,
        "appointment_seen_count",
        "appointment_scheduled_count",
        "Monthly GP appointment counts",
        "Excludes practices with fewer than 500 eligible patients in each month",
        "Number of appointments",
        COUNT_OUTPUT_FILE,
    )
    plot_trend(
        data,
        "appointment_seen_rate",
        "appointment_scheduled_rate",
        "Monthly GP appointment rates",
        "Excludes practices with fewer than 500 eligible patients in each month",
        "Appointments per 1,000 eligible patients",
        RATE_OUTPUT_FILE,
    )


if __name__ == "__main__":
    main()
