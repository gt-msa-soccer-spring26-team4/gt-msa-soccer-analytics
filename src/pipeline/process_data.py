import pandas as pd
import numpy as np
from pathlib import Path

raw_path = Path("data/raw")
output_path = Path("data/processed")

# make sure processed folder exists
output_path.mkdir(parents=True, exist_ok=True)

print("Pipeline started")

DATA_DIR = Path("data")

statsbomb_dir = DATA_DIR / "raw/Statsbomb"

events = pd.read_parquet(statsbomb_dir / "events.parquet")
matches = pd.read_parquet(statsbomb_dir / "matches.parquet")
lineups = pd.read_parquet(statsbomb_dir / "lineups.parquet")

##################################################################################
# 1) Identify xG-parity matches (team level)
##################################################################################

# Shot events
shots = events.loc[events["type"] == "Shot"].copy()

# Team xG per match
team_match_xg = (
    shots.groupby(["match_id", "team"], as_index=False)
    .agg(
        team_xg=("shot_statsbomb_xg", "sum"),
        shots=("id", "count")
    )
)

# Match outcomes
match_outcomes = matches[
    ["match_id", "home_team", "away_team", "home_score", "away_score"]
].copy()

home_outcomes = match_outcomes.assign(
    team=match_outcomes["home_team"],
    opponent=match_outcomes["away_team"],
    goals_for=match_outcomes["home_score"],
    goals_against=match_outcomes["away_score"]
)

away_outcomes = match_outcomes.assign(
    team=match_outcomes["away_team"],
    opponent=match_outcomes["home_team"],
    goals_for=match_outcomes["away_score"],
    goals_against=match_outcomes["home_score"]
)

team_outcomes = pd.concat([home_outcomes, away_outcomes], ignore_index=True)

team_outcomes["outcome"] = np.where(
    team_outcomes["goals_for"] > team_outcomes["goals_against"], "Win",
    np.where(
        team_outcomes["goals_for"] < team_outcomes["goals_against"], "Loss",
        "Draw"
    )
)

team_outcomes = team_outcomes[["match_id", "team", "opponent", "outcome"]]

# Merge outcomes with xG
team_match = team_match_xg.merge(
    team_outcomes,
    on=["match_id", "team"],
    how="left"
)

# Add opponent xG
opp_xg = team_match_xg.rename(
    columns={"team": "opponent", "team_xg": "opp_xg"}
)

team_match = team_match.merge(
    opp_xg[["match_id", "opponent", "opp_xg"]],
    on=["match_id", "opponent"],
    how="left"
)

# xG difference
team_match["xg_diff"] = (team_match["team_xg"] - team_match["opp_xg"]).abs()

XG_PARITY_THRESHOLD = 0.3

xg_parity = team_match.loc[
    team_match["xg_diff"] <= XG_PARITY_THRESHOLD
].copy()

xg_parity = xg_parity[
    [
        "match_id",
        "team",
        "opponent",
        "team_xg",
        "opp_xg",
        "xg_diff",
        "shots",
        "outcome"
    ]
].sort_values(["match_id", "team"]).reset_index(drop=True)

xg_parity.to_csv(
    output_path / "xg_parity_matches.csv",
    index=False
)

print("Match universe data set exported.")

##################################################################################
# 2) Add information on touch (possession proxy) by position
##################################################################################
xg_parity_match_ids = xg_parity["match_id"].unique()

events_parity = events[
    events["match_id"].isin(xg_parity_match_ids)
].copy()

TOUCH_EVENTS = [
    "Ball Receipt*",
    "Pass",
    "Carry",
    "Dribble",
    "Shot"
]

touches = events_parity[
    events_parity["type"].isin(TOUCH_EVENTS)
].copy()

POSITION_BIN_MAP = {
    "Center Back": "Center Back",
    "Left Center Back": "Center Back",
    "Right Center Back": "Center Back",

    "Left Back": "Fullback",
    "Right Back": "Fullback",
    "Left Wing Back": "Fullback",
    "Right Wing Back": "Fullback",

    "Center Defensive Midfield": "Defensive Midfield",
    "Left Defensive Midfield": "Defensive Midfield",
    "Right Defensive Midfield": "Defensive Midfield",

    "Center Midfield": "Central Midfield",
    "Left Center Midfield": "Central Midfield",
    "Right Center Midfield": "Central Midfield",

    "Center Attacking Midfield": "Attacking Midfield",
    "Left Attacking Midfield": "Attacking Midfield",
    "Right Attacking Midfield": "Attacking Midfield",

    "Left Wing": "Wide Forward",
    "Right Wing": "Wide Forward",
    "Left Midfield": "Wide Forward",
    "Right Midfield": "Wide Forward",

    "Center Forward": "Striker",
    "Left Center Forward": "Striker",
    "Right Center Forward": "Striker",
    "Secondary Striker": "Striker",

    "Goalkeeper": "Goalkeeper",
}

touches["position_bin"] = touches["position"].map(POSITION_BIN_MAP)

# remove events with positions outside the bins
touches = touches.dropna(subset=["position_bin"])

team_match_position_touches = (
    touches
    .groupby(["match_id", "team", "position_bin"])
    .size()
    .reset_index(name="touches")
)

team_match_totals = (
    team_match_position_touches
    .groupby(["match_id", "team"])["touches"]
    .sum()
    .reset_index(name="team_touches")
)

team_match_position_touches = team_match_position_touches.merge(
    team_match_totals,
    on=["match_id", "team"],
    how="left"
)

team_match_position_touches["touch_share"] = (
    team_match_position_touches["touches"] /
    team_match_position_touches["team_touches"]
)

team_match_position_touches = team_match_position_touches.merge(
    xg_parity[["match_id", "team", "outcome"]],
    on=["match_id", "team"],
    how="left"
)

team_match_position_touches["outcome_binary"] = np.where(
    team_match_position_touches["outcome"] == "Win",
    "Win",
    "Non-Win"
)

team_match_position_touches.to_csv(
    output_path / "positional_touch_share.csv",
    index=False
)

print("Touch share data set exported.")

##################################################################################
# 3) Progressive actions (pass, carry) by position
##################################################################################

progressive_events = events[
    events["match_id"].isin(xg_parity_match_ids)
].copy()

PROGRESSION_EVENTS = ["Pass", "Carry"]

prog_events = progressive_events[
    progressive_events["type"].isin(PROGRESSION_EVENTS)
].copy()

prog_events["is_progressive"] = (
    (prog_events["type"] == "Pass") &
    (prog_events["pass_end_location_x"] - prog_events["location_x"] >= 10)
) | (
    (prog_events["type"] == "Carry") &
    (prog_events["carry_end_location_x"] - prog_events["location_x"] >= 10)
)

progressive_actions = prog_events[prog_events["is_progressive"]].copy()

progressive_actions["position_bin"] = progressive_actions["position"].map(POSITION_BIN_MAP)
progressive_actions = progressive_actions.dropna(subset=["position_bin"])

team_match_position_progressions = (
    progressive_actions
    .groupby(["match_id", "team", "position_bin"])
    .size()
    .reset_index(name="progressive_actions")
)

team_match_progression_totals = (
    team_match_position_progressions
    .groupby(["match_id", "team"])["progressive_actions"]
    .sum()
    .reset_index(name="team_progressive_actions")
)

team_match_position_progressions = team_match_position_progressions.merge(
    team_match_progression_totals,
    on=["match_id", "team"],
    how="left"
)

team_match_position_progressions["progressive_share"] = (
    team_match_position_progressions["progressive_actions"] /
    team_match_position_progressions["team_progressive_actions"]
)

team_match_position_progressions = team_match_position_progressions.merge(
    xg_parity[["match_id", "team", "outcome"]],
    on=["match_id", "team"],
    how="left"
)

team_match_position_progressions["outcome_binary"] = np.where(
    team_match_position_progressions["outcome"] == "Win",
    "Win",
    "Non-Win"
)

team_match_position_progressions.to_csv(
    output_path / "positional_progressive_actions_share.csv",
    index=False
)

print("Progression share data set exported.")


##################################################################################
# 4) Add information on distance progression by position
##################################################################################
# compute progressive distance
progressive_actions["progressive_distance"] = np.where(
    progressive_actions["type"] == "Pass",
    progressive_actions["pass_end_location_x"] - progressive_actions["location_x"],
    progressive_actions["carry_end_location_x"] - progressive_actions["location_x"]
)

# aggregate progressive distance by position
team_match_position_prog_distance = (
    progressive_actions
    .groupby(["match_id", "team", "position_bin"])["progressive_distance"]
    .sum()
    .reset_index(name="progressive_distance")
)

# team totals
team_match_prog_distance_totals = (
    team_match_position_prog_distance
    .groupby(["match_id", "team"])["progressive_distance"]
    .sum()
    .reset_index(name="team_progressive_distance")
)

# merge totals
team_match_position_prog_distance = team_match_position_prog_distance.merge(
    team_match_prog_distance_totals,
    on=["match_id", "team"],
    how="left"
)

# compute share
team_match_position_prog_distance["progressive_distance_share"] = (
    team_match_position_prog_distance["progressive_distance"] /
    team_match_position_prog_distance["team_progressive_distance"]
)

# add outcome
team_match_position_prog_distance = team_match_position_prog_distance.merge(
    xg_parity[["match_id", "team", "outcome"]],
    on=["match_id", "team"],
    how="left"
)

team_match_position_prog_distance["outcome_binary"] = np.where(
    team_match_position_prog_distance["outcome"] == "Win",
    "Win",
    "Non-Win"
)

team_match_position_prog_distance.to_csv(
    output_path / "positional_progressive_distance_share.csv",
    index=False
)

print("Distance progression by position set exported.")


##################################################################################
# 5) Wing vs Central progression
##################################################################################

progressive_actions["position_bin"] = progressive_actions["position"].map(POSITION_BIN_MAP)
progressive_actions = progressive_actions.dropna(subset=["position_bin"])

# classify zones (by pitch width)
def classify_zone(y):
    if y < 20 or y > 60:
        return "Wide"
    else:
        return "Central"
    
progressive_actions["zone"] = progressive_actions["location_y"].apply(classify_zone)

team_match_zone_counts = (
    progressive_actions
    .groupby(["match_id", "team", "position_bin", "zone"])
    .size()
    .reset_index(name="progressive_actions")
)

team_match_zone_totals = (
    team_match_zone_counts
    .groupby(["match_id", "team", "position_bin"])["progressive_actions"]
    .sum()
    .reset_index(name="position_total_progressive_actions")
)

team_match_zone_counts = team_match_zone_counts.merge(
    team_match_zone_totals,
    on=["match_id", "team", "position_bin"],
    how="left"
)

team_match_zone_counts["progressive_share"] = (
    team_match_zone_counts["progressive_actions"] /
    team_match_zone_counts["position_total_progressive_actions"]
)

zone_share = (
    team_match_zone_counts
    .pivot(
        index=["match_id", "team", "position_bin"],
        columns="zone",
        values="progressive_share"
    )
    .reset_index()
    .fillna(0)
)

zone_share = zone_share.rename(columns={
    "Wide": "wide_progression_share",
    "Central": "central_progression_share"
})


zone_share = zone_share.merge(
    xg_parity[["match_id", "team", "outcome"]],
    on=["match_id", "team"],
    how="left"
)

zone_share["outcome_binary"] = np.where(
    zone_share["outcome"] == "Win",
    "Win",
    "Non-Win"
)

zone_share.to_csv(
    output_path / "positional_wing_vs_central_progression_share.csv",
    index=False
)

print("Progression by wide vs central set exported.")


##################################################################################
# 6) Team-level metrics: team-level wide vs central progression
##################################################################################
team_level = xg_parity[["match_id", "team", "outcome"]].copy()

# filter to parity matches
progressive_events = events[events["match_id"].isin(xg_parity["match_id"])].copy()

# keep passes + carries
prog_events = progressive_events[progressive_events["type"].isin(["Pass", "Carry"])].copy()

# define progressive
prog_events["is_progressive"] = (
    (prog_events["type"] == "Pass") &
    (prog_events["pass_end_location_x"] - prog_events["location_x"] >= 10)
) | (
    (prog_events["type"] == "Carry") &
    (prog_events["carry_end_location_x"] - prog_events["location_x"] >= 10)
)

# filter
progressive_actions = prog_events[prog_events["is_progressive"]].copy()

def classify_zone(y):
    return "Wide" if (y < 20 or y > 60) else "Central"

progressive_actions["zone"] = progressive_actions["location_y"].apply(classify_zone)

team_prog_total = (
    progressive_actions
    .groupby(["match_id", "team"])
    .size()
    .reset_index(name="team_progressive_actions")
)

team_wide_prog = (
    progressive_actions[progressive_actions["zone"] == "Wide"]
    .groupby(["match_id", "team"])
    .size()
    .reset_index(name="wide_progressive_actions")
)

team_width = team_prog_total.merge(
    team_wide_prog,
    on=["match_id", "team"],
    how="left"
).fillna(0)

team_width["wide_progression_share"] = (
    team_width["wide_progressive_actions"] /
    team_width["team_progressive_actions"]
)

team_level = team_level.merge(
    team_width[["match_id", "team", "wide_progression_share"]],
    on=["match_id", "team"],
    how="left"
)

print("Team metric computed: wide percentage of play.")

##################################################################################
# 7) Team-level metrics: where teams operate in build-up vs advanced phases
#     -i .e., is it slow and structured build up (tiki taka) or direct (west brom vibes)
##################################################################################
TOUCH_EVENTS = [
    "Ball Receipt*", 
    "Pass", 
    "Carry", 
    "Dribble", 
    "Shot"
]

POSITION_BIN_MAP = {
    "Center Back": "Center Back",
    "Left Center Back": "Center Back",
    "Right Center Back": "Center Back",

    "Left Back": "Fullback",
    "Right Back": "Fullback",
    "Left Wing Back": "Fullback",
    "Right Wing Back": "Fullback",

    "Center Defensive Midfield": "Defensive Midfield",
    "Left Defensive Midfield": "Defensive Midfield",
    "Right Defensive Midfield": "Defensive Midfield",

    "Center Midfield": "Central Midfield",
    "Left Center Midfield": "Central Midfield",
    "Right Center Midfield": "Central Midfield",

    "Center Attacking Midfield": "Attacking Midfield",
    "Left Attacking Midfield": "Attacking Midfield",
    "Right Attacking Midfield": "Attacking Midfield",

    "Left Wing": "Wide Forward",
    "Right Wing": "Wide Forward",
    "Left Midfield": "Wide Forward",
    "Right Midfield": "Wide Forward",

    "Center Forward": "Striker",
    "Left Center Forward": "Striker",
    "Right Center Forward": "Striker",
    "Secondary Striker": "Striker",

    "Goalkeeper": "Goalkeeper",
}

touches = events[
    (events["match_id"].isin(xg_parity["match_id"])) &
    (events["type"].isin(TOUCH_EVENTS))
].copy()

touches["position_bin"] = touches["position"].map(POSITION_BIN_MAP)
touches = touches.dropna(subset=["position_bin"])

team_pos_touches = (
    touches
    .groupby(["match_id", "team", "position_bin"])
    .size()
    .reset_index(name="touches")
)

BUILD_UP = ["Center Back", "Fullback", "Defensive Midfield"]

team_pos_touches["phase"] = np.where(
    team_pos_touches["position_bin"].isin(BUILD_UP),
    "BuildUp",
    "Advanced"
)

team_phase = (
    team_pos_touches
    .groupby(["match_id", "team", "phase"])["touches"]
    .sum()
    .reset_index()
)

team_phase = team_phase.pivot(
    index=["match_id", "team"],
    columns="phase",
    values="touches"
).reset_index().fillna(0)

team_phase["build_up_share"] = (
    team_phase["BuildUp"] /
    (team_phase["BuildUp"] + team_phase["Advanced"])
)

team_level = team_level.merge(
    team_phase[["match_id", "team", "build_up_share"]],
    on=["match_id", "team"],
    how="left"
)

print("Team metric computed: build up percentage of play.")

team_level = team_level.sort_values(["match_id", "team"])

##################################################################################
# 8) Team-level metrics: position concentration by the team - is it fluiod or spread out
##################################################################################
pos_prog = pd.read_csv(
    output_path / "positional_progressive_actions_share.csv"
)

max_prog = (
    pos_prog
    .groupby(["match_id", "team"])["progressive_share"]
    .max()
    .reset_index(name="max_progression_share")
)

team_level = team_level.merge(
    max_prog,
    on=["match_id", "team"],
    how="left"
)

print("Team metric computed: concentration of progressive possestion done.")


##################################################################################
# 9) Team-level metrics: what is the central midfield doing?
##################################################################################

pos_touch = pd.read_csv(
    output_path / "positional_touch_share.csv"
)

MIDFIELD = ["Central Midfield", "Attacking Midfield"]

midfield = pos_touch[
    pos_touch["position_bin"].isin(MIDFIELD)
]

midfield_share = (
    midfield
    .groupby(["match_id", "team"])["touch_share"]
    .sum()
    .reset_index(name="central_midfield_touch_share")
)

team_level = team_level.merge(
    midfield_share,
    on=["match_id", "team"],
    how="left"
)

print("Team metric computed: central midfield control done.")


team_level = team_level.sort_values(["match_id", "team"])

team_level.to_csv(
    output_path / "team_level_metrics.csv",
    index=False
)

print("Pipeline finished.")