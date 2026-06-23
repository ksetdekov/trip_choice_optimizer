from dataclasses import dataclass
from datetime import datetime, timedelta

import pandas as pd

from mvsampling.mvsampling import HandsTable


@dataclass
class RecommendationResult:
    optimization: dict
    variants: list
    samples: list
    ranking: pd.DataFrame

    @property
    def best_variant_name(self):
        if self.ranking.empty:
            return None
        return self.ranking.iloc[0]["name"]

    @property
    def best_variant_id(self):
        best_name = self.best_variant_name
        for variant_id, variant_name, _ in self.variants:
            if variant_name == best_name:
                return variant_id
        return None


def _parse_sample_datetime(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def build_events(samples):
    events = {}
    for sample_id, _, _, variant_name, option_value, change_datetime in samples:
        event_time = _parse_sample_datetime(change_datetime)
        event_time = event_time + timedelta(microseconds=int(sample_id) % 1000000)
        events[event_time] = (variant_name, float(option_value))
    return events


def build_table(optimization, variants, samples):
    variant_names = [variant_name for _, variant_name, _ in variants]
    table = HandsTable(
        options_list=variant_names,
        minimize=optimization["objective"] == "minimize",
        rho=float(optimization["rho"]),
    )
    events = build_events(samples)
    ranking = table.process_events(events, days=int(optimization["recency_days"]))
    return table, ranking


def get_recommendation(db, user_id, optimization_id):
    optimization = db.get_optimization_config(optimization_id, user_id=user_id)
    if optimization is None:
        raise ValueError("Optimization was not found.")

    variants = db.get_variants_by_optimization_id(optimization_id)
    if not variants:
        raise ValueError("Add at least one option before asking for a recommendation.")

    samples = db.get_samples_for_optimization_id(optimization_id)
    _, ranking = build_table(optimization, variants, samples)
    return RecommendationResult(
        optimization=optimization,
        variants=variants,
        samples=samples,
        ranking=ranking,
    )


def get_active_or_only_optimization_id(db, user_id):
    active_optimization_id = db.get_active_optimization_id(user_id)
    if active_optimization_id is not None:
        config = db.get_optimization_config(active_optimization_id, user_id=user_id)
        if config is not None:
            return active_optimization_id

    optimizations = db.get_optimizations(user_id)
    if len(optimizations) == 1:
        optimization_id = optimizations[0][2]
        db.set_active_optimization(user_id, optimization_id)
        return optimization_id

    return None


def format_ranking_table(recommendation, max_rows=5):
    ranking = recommendation.ranking.head(max_rows).copy()
    if ranking.empty:
        return "No options yet."

    output = pd.DataFrame({
        "option": ranking["name"],
        "n": ranking["Te"].astype(int),
        "mean": ranking["mu"].round(2),
        "risk95": ranking["var95"].round(2),
    })
    return output.to_string(index=False)
