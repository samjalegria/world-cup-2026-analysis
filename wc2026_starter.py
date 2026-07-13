"""
World Cup 2026 Team Performance Dashboard — v2
------------------------------------------------
Matches the ACTUAL columns in swaptr/fifa-wc-2026-matches:
round, gameweek, dayofweek, date, start_time, home_team, away_team,
score, home_score, away_score, attendance, venue, referee,
home_formation, away_formation, home_captain, away_captain,
home_possession, away_possession, home_sot, away_sot,
home_total_shots, away_total_shots, home_saves, away_saves,
home_cards_yellow, away_cards_yellow, home_cards_red, away_cards_red,
home_fouls, away_fouls, home_corners, away_corners, home_crosses,
away_crosses, home_interceptions, away_interceptions,
home_offsides, away_offsides, notes

No xG column exists in this dataset, so we use shot conversion rate
(goals per shot on target) as the efficiency metric instead.
"""

import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------------------------------------
# STEP 1: Load
# -----------------------------------------------------------
def load_data(csv_path="./data/matches.csv"):
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


# -----------------------------------------------------------
# STEP 2: Reshape match-level data into team-level long format
# (one row per team per match, instead of one row per match)
# -----------------------------------------------------------
def reshape_to_team_rows(df):
    home = df.rename(columns={
        "home_team": "team", "away_team": "opponent",
        "home_score": "goals", "away_score": "goals_against",
        "home_sot": "shots_on_target", "home_total_shots": "total_shots",
        "home_possession": "possession",
    })
    home["venue_type"] = "home"

    away = df.rename(columns={
        "away_team": "team", "home_team": "opponent",
        "away_score": "goals", "home_score": "goals_against",
        "away_sot": "shots_on_target", "away_total_shots": "total_shots",
        "away_possession": "possession",
    })
    away["venue_type"] = "away"

    keep_cols = [
        "date", "team", "opponent", "goals", "goals_against",
        "shots_on_target", "total_shots", "possession", "venue_type", "round",
    ]
    keep_cols = [c for c in keep_cols if c in home.columns]

    long_df = pd.concat([home[keep_cols], away[keep_cols]], ignore_index=True)
    long_df = long_df.sort_values(["team", "date"])
    return long_df


# -----------------------------------------------------------
# STEP 3: Feature engineering
# -----------------------------------------------------------
def add_performance_metrics(df):
    # Shot conversion rate: goals per shot on target (avoid divide-by-zero)
    df["conversion_rate"] = df.apply(
        lambda r: r["goals"] / r["shots_on_target"] if r["shots_on_target"] > 0 else 0,
        axis=1,
    )

    # Rolling form: average goals over each team's last 3 matches
    df["rolling_form"] = (
        df.groupby("team")["goals"]
        .transform(lambda x: x.rolling(window=3, min_periods=1).mean())
    )

    return df


# -----------------------------------------------------------
# STEP 4: Summary — who's most efficient in front of goal
# -----------------------------------------------------------
def performance_summary(df):
    summary = (
        df.groupby("team")
        .agg(
            matches=("goals", "count"),
            total_goals=("goals", "sum"),
            total_shots_on_target=("shots_on_target", "sum"),
            avg_possession=("possession", "mean"),
            latest_form=("rolling_form", "last"),
        )
        .reset_index()
    )

    summary["conversion_rate"] = (
        summary["total_goals"] / summary["total_shots_on_target"]
    ).fillna(0)

    summary = summary.sort_values("conversion_rate", ascending=False)
    return summary


# -----------------------------------------------------------
# STEP 5: Visualization
# -----------------------------------------------------------
def plot_conversion_rate(summary, top_n=10):
    top = summary.head(top_n)
    plt.figure(figsize=(10, 6))
    plt.barh(top["team"], top["conversion_rate"], color="#1F3864")
    plt.xlabel("Goals per Shot on Target")
    plt.title("World Cup 2026 — Most Clinical Teams (Shot Conversion Rate)")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig("conversion_rate_chart.png", dpi=150)
    plt.show()


# -----------------------------------------------------------
# RUN
# -----------------------------------------------------------
if __name__ == "__main__":
    df = load_data()
    df = reshape_to_team_rows(df)
    df = add_performance_metrics(df)
    summary = performance_summary(df)

    print(summary.head(10))
    plot_conversion_rate(summary)