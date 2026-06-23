import tempfile
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from services.recommendations import build_table, get_recommendation


def _new_png_path(prefix):
    output = tempfile.NamedTemporaryFile(
        prefix=prefix,
        suffix=".png",
        delete=False,
    )
    output.close()
    return output.name


def _samples_to_dataframe(samples):
    return pd.DataFrame(
        samples,
        columns=[
            "sample_id",
            "optimization_id",
            "variant_id",
            "variant",
            "value",
            "change_datetime",
        ],
    )


def render_probability_plot(db, user_id, optimization_id, iterations=1000):
    recommendation = get_recommendation(db, user_id, optimization_id)
    table, _ = build_table(
        recommendation.optimization,
        recommendation.variants,
        recommendation.samples,
    )

    counts = defaultdict(int)
    for _ in range(iterations):
        ranking = table.grade()
        counts[ranking.iloc[0]["name"]] += 1

    options = [variant_name for _, variant_name, _ in recommendation.variants]
    probabilities = [counts[option] / iterations for option in options]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(options, probabilities)
    ax.set_ylim(0, 1)
    ax.set_ylabel("First-place probability")
    ax.set_title(f"{recommendation.optimization['optimization_name']}: recommendation probability")
    ax.tick_params(axis="x", labelrotation=25)
    fig.tight_layout()

    path = _new_png_path("bandit_probability_")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_distribution_plot(db, user_id, optimization_id):
    recommendation = get_recommendation(db, user_id, optimization_id)
    df = _samples_to_dataframe(recommendation.samples)
    fig, ax = plt.subplots(figsize=(8, 4.5))

    if df.empty:
        ax.text(0.5, 0.5, "No logged values yet", ha="center", va="center")
        ax.set_axis_off()
    else:
        option_names = [variant_name for _, variant_name, _ in recommendation.variants]
        groups = []
        labels = []
        for option_name in option_names:
            values = df[df["variant"] == option_name]["value"].astype(float).to_numpy()
            if len(values) > 0:
                groups.append(values)
                labels.append(option_name)

        positions = list(range(1, len(labels) + 1))
        ax.violinplot(groups, positions=positions, showmeans=True)
        ax.set_xticks(positions)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ylabel = "Value"
        if recommendation.optimization["metric_type"] == "time":
            ylabel = "Minutes"
        ax.set_ylabel(ylabel)
        ax.set_title(f"{recommendation.optimization['optimization_name']}: logged values")

    fig.tight_layout()
    path = _new_png_path("bandit_distribution_")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_timeline_plot(db, user_id, optimization_id):
    recommendation = get_recommendation(db, user_id, optimization_id)
    df = _samples_to_dataframe(recommendation.samples)
    fig, ax = plt.subplots(figsize=(8, 4.5))

    if df.empty:
        ax.text(0.5, 0.5, "No logged values yet", ha="center", va="center")
        ax.set_axis_off()
    else:
        df["change_datetime"] = pd.to_datetime(df["change_datetime"])
        df["value"] = df["value"].astype(float)
        for variant_name, group in df.groupby("variant"):
            ax.scatter(group["change_datetime"], group["value"], label=variant_name)
        ylabel = "Value"
        if recommendation.optimization["metric_type"] == "time":
            ylabel = "Minutes"
        ax.set_ylabel(ylabel)
        ax.set_title(f"{recommendation.optimization['optimization_name']}: recent values")
        ax.legend()
        fig.autofmt_xdate()

    fig.tight_layout()
    path = _new_png_path("bandit_timeline_")
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def render_all_plots(db, user_id, optimization_id):
    return [
        render_probability_plot(db, user_id, optimization_id),
        render_distribution_plot(db, user_id, optimization_id),
        render_timeline_plot(db, user_id, optimization_id),
    ]
