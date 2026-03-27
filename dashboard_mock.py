import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import FontManager, PyPizza
import polars as pl
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Positional Level Impact in xG-Parity Matches",
    initial_sidebar_state="collapsed",
)

# ── Color palette ─────────────────────────────────────────────────────────────
BG_MAIN    = "#0E1117"
BG_PANEL   = "#161B22"
BG_DARK    = "#1B1B1B"
ACCENT     = "#1A78CF"   # unified blue accent
CORAL      = "lightcoral"
BLUE       = "#1A78CF"
GREY       = "#888888"
WHITE      = "#F2F2F2"
TEXT       = "#E6EDF3"
TEXT_MUTED = "#8B949E"
BORDER     = "#1A78CF33"  # blue at 20% opacity for subtle borders

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Shell ── */
.stApp {{ background-color: {BG_MAIN}; }}
.block-container {{
    padding-top: 1.2rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}}
[data-testid="collapsedControl"] {{ display: none; }}

/* ── Typography ── */
h1, h2, h3 {{ color: {TEXT} !important; margin-bottom: 0 !important; }}
p, li {{ color: {TEXT_MUTED}; }}
hr {{ border-color: #30363D !important; margin: 0.4rem 0 !important; }}
label {{ color: {TEXT_MUTED} !important; font-size: 0.72rem !important;
         letter-spacing: 0.07em; text-transform: uppercase; }}

/* ── Tabs — replace Streamlit accent with blue ── */
[data-baseweb="tab-highlight"] {{ background-color: {ACCENT} !important; }}
button[data-baseweb="tab"] {{ color: {TEXT_MUTED} !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{ color: {TEXT} !important; }}
[data-baseweb="tab-list"] {{ background-color: {BG_MAIN} !important;
                             border-bottom: 1px solid #30363D; }}

/* ── Inputs — replace Streamlit green/red focus with blue ── */
[data-baseweb="select"] > div:focus-within,
[data-baseweb="input"] > div:focus-within {{
    border-color: {ACCENT} !important;
    box-shadow: 0 0 0 1px {ACCENT} !important;
}}
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {{
    background-color: {BG_PANEL} !important;
    border-color: #30363D !important;
    color: {TEXT} !important;
}}
[data-baseweb="select"] * {{ color: {TEXT} !important; }}
[data-baseweb="popover"] {{ background-color: {BG_PANEL} !important; }}

/* ── Misc components ── */
[data-testid="stImage"] img {{ border-radius: 6px; }}

/* ── Stat card ── */
.stat-card {{
    background: {BG_PANEL};
    border: 1px solid {ACCENT}44;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: center;
}}
.stat-label {{ color: {TEXT_MUTED}; font-size: 0.68rem; letter-spacing: 0.09em;
               text-transform: uppercase; margin-bottom: 3px; }}
.stat-value {{ color: {TEXT}; font-size: 1.6rem; font-weight: 700; line-height: 1.1; }}

/* ── Placeholder box ── */
.placeholder-box {{
    border: 1px dashed {ACCENT}88;
    border-radius: 8px;
    padding: 10px 16px;
    background: {BG_PANEL};
    color: {TEXT_MUTED};
    font-size: 0.80rem;
    letter-spacing: 0.03em;
}}
</style>
""", unsafe_allow_html=True)

# ── Fonts ─────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_fonts():
    fn = FontManager(
        "https://raw.githubusercontent.com/googlefonts/roboto/main/src/hinted/Roboto-Regular.ttf"
    )
    fb = FontManager(
        "https://raw.githubusercontent.com/google/fonts/main/apache/robotoslab/RobotoSlab[wght].ttf"
    )
    return fn, fb

font_normal, font_bold = load_fonts()

# ── Data loading ──────────────────────────────────────────────────────────────
DATA_DIR = Path("data")

@st.cache_data
def load_processed_data():
    touch_share        = pl.read_csv(DATA_DIR / "processed" / "positional_touch_share.csv")
    prog_actions_share = pl.read_csv(DATA_DIR / "processed" / "positional_progressive_actions_share.csv")
    prog_dist_share    = pl.read_csv(DATA_DIR / "processed" / "positional_progressive_distance_share.csv")
    wing_vs_central    = pl.read_csv(DATA_DIR / "processed" / "positional_wing_vs_central_progression_share.csv")
    xg_parity          = pl.read_csv(DATA_DIR / "processed" / "xg_parity_matches.csv")
    matches            = pl.read_parquet(DATA_DIR / "Statsbomb" / "matches.parquet")
    return touch_share, prog_actions_share, prog_dist_share, wing_vs_central, xg_parity, matches

touch_share, prog_actions_share, prog_dist_share, wing_vs_central, xg_parity, matches = load_processed_data()

match_seasons     = matches.select(["match_id", "season_name"]).unique()
touch_share_s     = touch_share.join(match_seasons, on="match_id", how="left")
prog_actions_s    = prog_actions_share.join(match_seasons, on="match_id", how="left")
wing_vs_central_s = wing_vs_central.join(match_seasons, on="match_id", how="left")
xg_parity_s       = xg_parity.join(match_seasons, on="match_id", how="left")

# ── Pizza constants ───────────────────────────────────────────────────────────
METRICS = [
    "touch_share", "touches", "progressive_share", "progressive_distance_share",
    "prog_dist_per_action", "central_progression_share", "wide_progression_share",
]
METRIC_LABELS = [
    "Touch Share", "Touch Volume", "Progressive\nAction Share", "Progressive\nDistance Share",
    "Prog. Distance\nper Action", "Central\nProgression", "Wide\nProgression",
]
POS_BINS_BY_GROUP = {
    "GK":  ["Goalkeeper"],
    "Def": ["Center Back", "Fullback"],
    "Mid": ["Defensive Midfield", "Central Midfield", "Attacking Midfield"],
    "Att": ["Wide Forward", "Striker"],
}
GROUP_FULL_NAMES = {
    "GK":  "Goalkeeper",
    "Def": "Defenders",
    "Mid": "Midfielders",
    "Att": "Attackers",
}
PIZZA_KWARGS = dict(
    background_color=BG_DARK,
    straight_line_color="#3A3E47", straight_line_lw=1,
    last_circle_lw=1, last_circle_color="#3A3E47",
    other_circle_ls="-.", other_circle_lw=0.8,
)
KW_NONWIN = dict(facecolor=BLUE,  edgecolor="#3A3E47", zorder=2, linewidth=1)
KW_WIN    = dict(facecolor=CORAL, edgecolor="#3A3E47", zorder=2, linewidth=1)
KW_PARAMS = dict(color=TEXT_MUTED, fontsize=7, fontproperties=font_normal.prop, va="center")
KW_VALS   = dict(color=WHITE, fontsize=7, fontproperties=font_normal.prop, zorder=3,
                 bbox=dict(edgecolor="#3A3E47", facecolor="#1A4A7A",
                           boxstyle="round,pad=0.2", lw=1))
KW_CVALS  = dict(color=WHITE, fontsize=7, fontproperties=font_normal.prop, zorder=3,
                 bbox=dict(edgecolor="#3A3E47", facecolor="#8B3030",
                           boxstyle="round,pad=0.2", lw=1))

# ── Touch share dumbbell data (module-level cache) ────────────────────────────
@st.cache_data
def build_touch_dumbbell_data(year: str):
    ts = touch_share_s if year == "All Years" else touch_share_s.filter(pl.col("season_name") == year)
    league_agg = (
        ts
        .group_by("position_bin")
        .agg(pl.col("touch_share").mean().alias("league_avg"))
        .sort("league_avg", descending=True)
    )
    team_agg = (
        ts
        .group_by(["team", "position_bin", "outcome_binary"])
        .agg(pl.col("touch_share").mean().alias("touch_share"))
    )
    return league_agg.to_pandas(), team_agg.to_pandas()

# ── Pizza aggregations (module-level cache) ───────────────────────────────────
@st.cache_data
def build_pizza_aggs(year: str):
    base = (
        touch_share_s
        .join(
            prog_actions_s.select(["match_id", "team", "position_bin", "progressive_actions", "progressive_share"]),
            on=["match_id", "team", "position_bin"], how="left",
        )
        .join(
            prog_dist_share.select(["match_id", "team", "position_bin", "progressive_distance", "progressive_distance_share"]),
            on=["match_id", "team", "position_bin"], how="left",
        )
        .join(
            wing_vs_central.select(["match_id", "team", "position_bin", "central_progression_share", "wide_progression_share"]),
            on=["match_id", "team", "position_bin"], how="left",
        )
        .with_columns(
            # null-safe: returns null (not inf) when progressive_actions is 0
            pl.when(pl.col("progressive_actions") > 0)
            .then(pl.col("progressive_distance") / pl.col("progressive_actions").cast(pl.Float64))
            .otherwise(None)
            .alias("prog_dist_per_action")
        )
        .with_columns(
            pl.col("position_bin").replace({
                "Goalkeeper":         "GK",
                "Center Back":        "Def",
                "Fullback":           "Def",
                "Defensive Midfield": "Mid",
                "Central Midfield":   "Mid",
                "Attacking Midfield": "Mid",
                "Wide Forward":       "Att",
                "Striker":            "Att",
            }).alias("pos_group")
        )
    )
    if year != "All Years":
        base = base.filter(pl.col("season_name") == year)

    agg_exprs   = [pl.col(m).mean().alias(m) for m in METRICS]
    grouped_grp = base.group_by(["team", "pos_group",    "outcome_binary"]).agg(agg_exprs)
    grouped_bin = base.group_by(["team", "position_bin", "outcome_binary"]).agg(agg_exprs)
    return grouped_grp, grouped_bin

def _rank(subset: pl.DataFrame, team_name: str) -> list[int]:
    team_row = subset.filter(pl.col("team") == team_name)
    if team_row.is_empty():
        return [50] * len(METRICS)
    percentiles = []
    for m in METRICS:
        col_vals = subset[m].drop_nulls().to_list()
        team_val = team_row[m][0]
        if team_val is None or len(col_vals) == 0:
            percentiles.append(50)
        else:
            percentiles.append(int(round(sum(v <= team_val for v in col_vals) / len(col_vals) * 100)))
    return percentiles

def get_pct_group(grouped_grp, team_name, pos_grp, outcome):
    return _rank(
        grouped_grp.filter((pl.col("pos_group") == pos_grp) & (pl.col("outcome_binary") == outcome)),
        team_name,
    )

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h2 style='margin-bottom:2px'>Positional Level Impact in xG-Parity Matches</h2>"
    f"<p style='color:{TEXT_MUTED};font-size:0.78rem;margin:0 0 6px'>"
    f"Comparing positional possession structures across match outcomes in competitive, balanced fixtures</p>",
    unsafe_allow_html=True,
)
# ══════════════════════════════════════════════════════════════════════════════
# TEAM VIEW
# ══════════════════════════════════════════════════════════════════════════════

# ── Filters + legend (left) | cards (right) ──────────────────────────────────
all_teams = sorted(wing_vs_central_s["team"].unique().to_list())

col_left, col_right = st.columns([1, 1])

with col_left:
    f1, f2 = st.columns([1, 1])
    with f1:
        selected_team = st.selectbox("Team", ["All Teams"] + all_teams, index=0)
    with f2:
        if selected_team == "All Teams":
            team_years = sorted(
                wing_vs_central_s["season_name"].drop_nulls().unique().to_list()
            )
        else:
            team_years = sorted(
                wing_vs_central_s
                .filter(pl.col("team") == selected_team)["season_name"]
                .drop_nulls().unique().to_list()
            )
        selected_year = st.selectbox("Season", ["All Years"] + team_years, key="team_year")
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:20px;padding:8px 16px;"
        f"background:{BG_PANEL};border:1px solid {ACCENT}44;border-radius:8px;'>"
        f"<span style='color:{TEXT_MUTED};font-size:0.68rem;letter-spacing:0.09em;"
        f"text-transform:uppercase;white-space:nowrap;'>Legend</span>"
        f"<span style='display:flex;align-items:center;gap:7px;font-size:0.80rem;color:{WHITE};white-space:nowrap'>"
        f"<svg width='11' height='11' viewBox='0 0 12 12'><polygon points='6,0 12,6 6,12 0,6' fill='{GREY}'/></svg>"
        f"League Average</span>"
        f"<span style='display:flex;align-items:center;gap:7px;font-size:0.80rem;color:{WHITE};white-space:nowrap'>"
        f"<svg width='11' height='11'><circle cx='5.5' cy='5.5' r='4.5' fill='lightcoral' stroke='{WHITE}' stroke-width='1'/></svg>"
        f"Win</span>"
        f"<span style='display:flex;align-items:center;gap:7px;font-size:0.80rem;color:{WHITE};white-space:nowrap'>"
        f"<svg width='11' height='11'><circle cx='5.5' cy='5.5' r='4.5' fill='{BLUE}' stroke='{WHITE}' stroke-width='1'/></svg>"
        f"Non-Win</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

year_label = selected_year if selected_year != "All Years" else "All Seasons"

# ── Filter data ───────────────────────────────────────────────────────────────
wvc_filtered = wing_vs_central_s
if selected_year != "All Years":
    wvc_filtered = wvc_filtered.filter(pl.col("season_name") == selected_year)

# ── Stats ─────────────────────────────────────────────────────────────────────
if selected_team == "All Teams":
    n_matches = wvc_filtered["match_id"].n_unique()
else:
    n_matches = wvc_filtered.filter(pl.col("team") == selected_team)["match_id"].n_unique()

xg_filtered = xg_parity_s
if selected_team != "All Teams":
    xg_filtered = xg_filtered.filter(pl.col("team") == selected_team)
if selected_year != "All Years":
    xg_filtered = xg_filtered.filter(pl.col("season_name") == selected_year)

win_rate = (xg_filtered["outcome"] == "Win").sum() / max(len(xg_filtered), 1) * 100

def _card(label, value, val_style=""):
    return (
        f"<div class='stat-card' style='margin-bottom:8px;padding:8px 16px'>"
        f"<div class='stat-label'>{label}</div>"
        f"<div class='stat-value' style='{val_style}'>{value}</div>"
        f"</div>"
    )

with col_right:
    st.markdown(
        _card("Matches", n_matches) +
        _card("Win Rate", f"{win_rate:.0f}%"),
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Data prep ─────────────────────────────────────────────────────────────────
league_agg = (
    wvc_filtered
    .group_by("position_bin")
    .agg(pl.col("central_progression_share").mean().alias("central"))
    .sort("central", descending=True)
)
league_avg = dict(zip(league_agg["position_bin"].to_list(), league_agg["central"].to_list()))

team_agg_src = wvc_filtered if selected_team == "All Teams" else wvc_filtered.filter(pl.col("team") == selected_team)
team_agg = (
    team_agg_src
    .group_by(["position_bin", "outcome_binary"])
    .agg(pl.col("central_progression_share").mean().alias("central"))
)
team_win = dict(zip(
    team_agg.filter(pl.col("outcome_binary") == "Win")["position_bin"].to_list(),
    team_agg.filter(pl.col("outcome_binary") == "Win")["central"].to_list(),
))
team_nonwin = dict(zip(
    team_agg.filter(pl.col("outcome_binary") == "Non-Win")["position_bin"].to_list(),
    team_agg.filter(pl.col("outcome_binary") == "Non-Win")["central"].to_list(),
))

league_touch_df, team_touch_df = build_touch_dumbbell_data(selected_year)
touch_order  = league_touch_df["position_bin"].tolist()
league_touch = dict(zip(league_touch_df["position_bin"], league_touch_df["league_avg"]))

if selected_team == "All Teams":
    team_touch_src = team_touch_df.groupby(["position_bin", "outcome_binary"], as_index=False)["touch_share"].mean()
else:
    team_touch_src = team_touch_df[team_touch_df["team"] == selected_team]
touch_win_ts = dict(zip(
    team_touch_src[team_touch_src["outcome_binary"] == "Win"]["position_bin"],
    team_touch_src[team_touch_src["outcome_binary"] == "Win"]["touch_share"],
))
touch_nonwin_ts = dict(zip(
    team_touch_src[team_touch_src["outcome_binary"] == "Non-Win"]["position_bin"],
    team_touch_src[team_touch_src["outcome_binary"] == "Non-Win"]["touch_share"],
))

POS_DEPTH = {
    "Goalkeeper":         0.0,
    "Center Back":        1.0,
    "Fullback":           1.9,
    "Defensive Midfield": 3.2,
    "Central Midfield":   4.2,
    "Attacking Midfield": 5.2,
    "Wide Forward":       6.1,
    "Striker":            7.0,
}
ALL_POS = list(POS_DEPTH.keys())

grouped_grp, grouped_bin = build_pizza_aggs(selected_year)

# ── Row 1: Touch Share | Central (shared Y-axis) ─────────────────────────────
col_touch, col_central = st.columns([1, 1])

YTICKS    = [POS_DEPTH[p] for p in ALL_POS]
YLIM      = (-0.6, 7.5)
SPINE_COL = "#2E323A"
GRID_KW   = dict(axis="x", color=SPINE_COL, lw=0.6, zorder=0)

with col_touch:
    fig_ts, ax_ts = plt.subplots(figsize=(5, 3.5))
    fig_ts.patch.set_alpha(0)
    ax_ts.set_facecolor(BG_DARK)
    ax_ts.grid(**GRID_KW)
    for pos in ALL_POS:
        y  = POS_DEPTH[pos]
        lv = league_touch.get(pos)
        bw = touch_win_ts.get(pos)
        bn = touch_nonwin_ts.get(pos)
        if bw is not None and bn is not None:
            ax_ts.plot([bw, bn], [y, y], color=WHITE, lw=1.2, alpha=0.4, zorder=2)
        if lv is not None:
            ax_ts.scatter(lv, y, color=GREY, s=60, zorder=3, marker="D")
        if bw is not None:
            ax_ts.scatter(bw, y, color=CORAL, s=100, zorder=4, edgecolors=WHITE, linewidths=0.8)
        if bn is not None:
            ax_ts.scatter(bn, y, color=BLUE, s=100, zorder=4, edgecolors=WHITE, linewidths=0.8)
    ax_ts.set_yticks(YTICKS)
    ax_ts.set_yticklabels(ALL_POS, color=WHITE, fontsize=8, fontproperties=font_normal.prop)
    ax_ts.set_ylim(*YLIM)
    ax_ts.tick_params(axis="x", colors=GREY, labelsize=8)
    ax_ts.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax_ts.set_xlabel("Touch Share", color=TEXT_MUTED, fontsize=8,
                     fontproperties=font_normal.prop, labelpad=4)
    for spine in ax_ts.spines.values():
        spine.set_edgecolor(SPINE_COL)
    ax_ts.set_title("Touch Share", color=WHITE, fontsize=10, pad=6,
                    fontproperties=font_bold.prop)
    plt.tight_layout()
    st.pyplot(fig_ts, use_container_width=True)
    plt.close(fig_ts)

with col_central:
    fig_db, ax = plt.subplots(figsize=(5, 3.5))
    fig_db.patch.set_alpha(0)
    ax.set_facecolor(BG_DARK)
    ax.grid(**GRID_KW)
    ax.axvspan(0.0,  0.38, color="#1A78CF",    alpha=0.06, zorder=0)
    ax.axvspan(0.38, 0.62, color="#FFFFFF",     alpha=0.03, zorder=0)
    ax.axvspan(0.62, 1.0,  color="lightcoral", alpha=0.06, zorder=0)
    for x, label in [(0.19, "Wide"), (0.50, "Mixed"), (0.81, "Central")]:
        ax.text(x, 7.2, label, color=GREY, fontsize=7, ha="center", va="bottom",
                fontproperties=font_normal.prop)
    for pos in ALL_POS:
        y  = POS_DEPTH[pos]
        lv = league_avg.get(pos)
        bw = team_win.get(pos)
        bn = team_nonwin.get(pos)
        if bw is not None and bn is not None:
            ax.plot([bw, bn], [y, y], color=WHITE, lw=1.2, alpha=0.4, zorder=2)
        if lv is not None:
            ax.scatter(lv, y, color=GREY, s=60, zorder=3, marker="D")
        if bw is not None:
            ax.scatter(bw, y, color=CORAL, s=100, zorder=4, edgecolors=WHITE, linewidths=0.8)
        if bn is not None:
            ax.scatter(bn, y, color=BLUE, s=100, zorder=4, edgecolors=WHITE, linewidths=0.8)
    ax.axvline(0.5, color=GREY, lw=0.8, ls="--", alpha=0.4, zorder=1)
    ax.set_yticks(YTICKS)
    ax.set_yticklabels([])
    ax.set_ylim(*YLIM)
    ax.set_xlim(0.0, 1.0)
    ax.tick_params(axis="x", colors=GREY, labelsize=8)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_xlabel("← Wide  ·  Central Share  ·  Central →",
                  color=TEXT_MUTED, fontsize=8, fontproperties=font_normal.prop, labelpad=4)
    for spine in ax.spines.values():
        spine.set_edgecolor(SPINE_COL)
    ax.set_title("Central vs Wide Progression", color=WHITE, fontsize=10, pad=6,
                 fontproperties=font_bold.prop)
    plt.tight_layout()
    st.pyplot(fig_db, use_container_width=True)
    plt.close(fig_db)

# ── Row 2: four pizzas — GK | Def | Mid | Att ────────────────────────────────
st.markdown(
    f"<p style='color:{TEXT_MUTED};font-size:0.72rem;letter-spacing:0.09em;"
    f"text-transform:uppercase;margin:6px 0 2px'>Percentile Ranks</p>",
    unsafe_allow_html=True,
)
pizza_cols = st.columns([1, 1, 1, 1])
KW_PARAMS_SM = dict(color=TEXT_MUTED, fontsize=5.5, fontproperties=font_normal.prop, va="center")
KW_VALS_SM   = dict(color=WHITE, fontsize=5.5, fontproperties=font_normal.prop, zorder=3,
                    bbox=dict(edgecolor="#3A3E47", facecolor="#1A4A7A",
                              boxstyle="round,pad=0.2", lw=1))
KW_CVALS_SM  = dict(color=WHITE, fontsize=5.5, fontproperties=font_normal.prop, zorder=3,
                    bbox=dict(edgecolor="#3A3E47", facecolor="#8B3030",
                              boxstyle="round,pad=0.2", lw=1))

for col, grp in zip(pizza_cols, POS_BINS_BY_GROUP.keys()):
    with col:
        fig_pz, ax_pz = plt.subplots(figsize=(3.5, 3.5), subplot_kw=dict(projection="polar"))
        fig_pz.patch.set_alpha(0)
        ax_pz.set_facecolor(BG_DARK)
        PyPizza(params=METRIC_LABELS, **PIZZA_KWARGS).make_pizza(
            get_pct_group(grouped_grp, selected_team, grp, "Non-Win"),
            compare_values=get_pct_group(grouped_grp, selected_team, grp, "Win"),
            ax=ax_pz,
            kwargs_slices=KW_NONWIN, kwargs_compare=KW_WIN,
            kwargs_params=KW_PARAMS_SM, kwargs_values=KW_VALS_SM,
            kwargs_compare_values=KW_CVALS_SM,
        )
        fig_pz.suptitle(GROUP_FULL_NAMES[grp], fontproperties=font_bold.prop,
                        fontsize=9, color=WHITE, y=1.0)
        plt.tight_layout(rect=[0, 0, 1, 0.985])
        st.pyplot(fig_pz, use_container_width=True)
        plt.close(fig_pz)
