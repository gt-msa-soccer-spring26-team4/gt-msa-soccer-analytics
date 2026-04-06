import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mplsoccer import Pitch, PyPizza, FontManager
import polars as pl
from pathlib import Path
import numpy as np

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Trilemma Soccer Analytics",
    initial_sidebar_state="expanded",
)

# ── Color palette ─────────────────────────────────────────────────────────────
BG_MAIN    = "#0E1117"
BG_PANEL   = "#161B22"
BG_PITCH   = "#0D1B2A"
LINE_PITCH = "#2E4057"
ACCENT     = "#E05C5C"
TEXT       = "#E6EDF3"
TEXT_MUTED = "#8B949E"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* shell */
.stApp {{ background-color: {BG_MAIN}; }}
/* remove default top padding so header sits tight */
.block-container {{ padding-top: 1.2rem !important; padding-bottom: 0.5rem !important; }}
/* sidebar */
[data-testid="stSidebar"] {{
    background-color: {BG_PANEL};
    border-right: 1px solid #30363D;
}}
[data-testid="stSidebar"] * {{ color: {TEXT} !important; }}
/* labels */
label {{ color: {TEXT_MUTED} !important; font-size: 0.75rem !important;
         letter-spacing: 0.07em; text-transform: uppercase; }}
/* headings */
h2, h3 {{ color: {TEXT} !important; margin-bottom: 0 !important; }}
/* dividers */
hr {{ border-color: #30363D !important; margin: 0.5rem 0 !important; }}
/* stat cards */
.stat-card {{
    background: {BG_PANEL}; border: 1px solid #30363D; border-radius: 8px;
    padding: 10px 14px; text-align: center;
}}
.stat-label {{ color: {TEXT_MUTED}; font-size: 0.68rem; letter-spacing: 0.09em;
               text-transform: uppercase; margin-bottom: 2px; }}
.stat-value {{ color: {TEXT}; font-size: 1.5rem; font-weight: 700; line-height: 1.15; }}
/* sidebar metric cards */
.side-card {{
    background: {BG_MAIN}; border: 1px solid #30363D; border-radius: 6px;
    padding: 8px 12px; margin-bottom: 6px;
}}
.side-label {{ color: {TEXT_MUTED}; font-size: 0.66rem; letter-spacing: 0.08em;
               text-transform: uppercase; }}
.side-value {{ color: {TEXT}; font-size: 1.15rem; font-weight: 600; }}
/* chart label row */
.chart-label {{ color: {TEXT_MUTED}; font-size: 0.70rem; letter-spacing: 0.07em;
                text-transform: uppercase; margin-bottom: 2px; }}
/* pyplot images */
[data-testid="stImage"] img {{ border-radius: 6px; }}
/* apply button */
div[data-testid="stFormSubmitButton"] > button {{
    width: 100%; background: #238636; color: white; border: none;
    border-radius: 6px; padding: 8px; font-weight: 600; font-size: 0.85rem;
    cursor: pointer;
}}
div[data-testid="stFormSubmitButton"] > button:hover {{ background: #2ea043; }}
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

# ── Data loading + xG-parity pre-filter ──────────────────────────────────────
DATA_DIR = Path("data/Statsbomb")
XG_PARITY_THRESHOLD = 0.3

@st.cache_data
def load_parity_data():
    """Load events & matches, pre-filter events to xG-parity matches only."""
    events  = pl.read_parquet(DATA_DIR / "events.parquet")
    matches = pl.read_parquet(DATA_DIR / "matches.parquet")

    # Build xG per team per match from shots
    shots = events.filter(pl.col("type") == "Shot")
    team_xg = shots.group_by(["match_id", "team_id"]).agg(
        pl.col("shot_statsbomb_xg").sum().alias("total_xg")
    )
    ta = team_xg.rename({"team_id": "team_a", "total_xg": "xg_a"})
    tb = team_xg.rename({"team_id": "team_b", "total_xg": "xg_b"})
    pairs = ta.join(tb, on="match_id").filter(pl.col("team_a") != pl.col("team_b"))
    parity_ids = (
        pairs.with_columns((pl.col("xg_a") - pl.col("xg_b")).abs().alias("xg_diff"))
        .filter(pl.col("xg_diff") <= XG_PARITY_THRESHOLD)["match_id"]
        .unique().to_list()
    )

    # Pre-filter to parity pool — subsequent queries hit this smaller frame
    events_p = events.filter(pl.col("match_id").is_in(parity_ids))
    return events_p, matches, parity_ids

events_p, matches_all, parity_ids = load_parity_data()
parity_id_set = set(parity_ids)

# ── Cached lookup helpers ─────────────────────────────────────────────────────

@st.cache_data
def all_parity_players() -> list[str]:
    return sorted(
        events_p.filter(pl.col("player").is_not_null())["player"].unique().to_list()
    )

@st.cache_data
def seasons_for_player(player: str) -> list[str]:
    """Seasons where the player appeared in xG-parity matches."""
    mids = events_p.filter(pl.col("player") == player)["match_id"].unique().to_list()
    seasons = (
        matches_all.filter(pl.col("match_id").is_in(mids))["season_name"]
        .unique().to_list()
    )
    return sorted(seasons)

@st.cache_data
def player_parity_events(player: str, season: str, condition: str) -> pl.DataFrame:
    """
    Return events for *player* in xG-parity matches, optionally restricted by
    season and match outcome condition.  All heavy filtering is done here so
    downstream code stays lightweight.
    """
    # Season filter
    if season == "All Seasons":
        candidate_ids = parity_ids
    else:
        season_mids = matches_all.filter(
            pl.col("season_name") == season
        )["match_id"].to_list()
        candidate_ids = list(parity_id_set & set(season_mids))

    pe = events_p.filter(
        (pl.col("player") == player) & pl.col("match_id").is_in(candidate_ids)
    )
    if pe.is_empty() or condition == "All":
        return pe

    # Win/non-win filter — determine player's team result per match
    player_team = pe.select(["match_id", "team_id"]).unique()
    match_df = matches_all.filter(pl.col("match_id").is_in(candidate_ids)).select(
        ["match_id", "home_team_id", "away_team_id", "home_score", "away_score"]
    )
    joined = player_team.join(match_df, on="match_id").with_columns(
        pl.when(
            ((pl.col("team_id") == pl.col("home_team_id")) & (pl.col("home_score") > pl.col("away_score")))
            | ((pl.col("team_id") == pl.col("away_team_id")) & (pl.col("away_score") > pl.col("home_score")))
        ).then(pl.lit("win")).otherwise(pl.lit("non-win")).alias("result")
    )
    result_label = "win" if condition == "Wins" else "non-win"
    win_mids = joined.filter(pl.col("result") == result_label)["match_id"].to_list()
    return pe.filter(pl.col("match_id").is_in(win_mids))


# ── Plot helpers ──────────────────────────────────────────────────────────────

CMAP_KDE = LinearSegmentedColormap.from_list(
    "pass_heat", [BG_PITCH, ACCENT, "#FFFFFF"], N=256
)

def _dark_fig(fig, *extra_axes):
    fig.patch.set_facecolor(BG_PANEL)
    for ax in extra_axes:
        if ax is not None:
            ax.set_facecolor(BG_PANEL)
    return fig

def plot_kde(passes: pl.DataFrame):
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=BG_PITCH,
        line_color=LINE_PITCH,
        line_zorder=2,
        linewidth=1,
    )
    fig, ax = pitch.draw(figsize=(9, 6))
    _dark_fig(fig)

    if not passes.is_empty():
        pitch.kdeplot(
            passes["pass_end_location_x"],
            passes["pass_end_location_y"],
            ax=ax,
            fill=True, levels=80, thresh=0.05,
            cmap=CMAP_KDE, alpha=0.85,
        )
    else:
        ax.text(60, 40, "No pass data", color=TEXT_MUTED, ha="center", va="center", fontsize=11)

    return fig


PIZZA_PARAMS = [
    "Touches", "Touch Share", "Passes", "Fwd Pass %",
    "Carry Distance", "Progressive Carries",
    "Final Third Entries", "Goal Creating Actions",
    "Shots", "xG / Shot",
]

def plot_pizza():
    rng = np.random.default_rng(42)
    values = rng.integers(15, 99, size=len(PIZZA_PARAMS)).tolist()

    baker = PyPizza(
        params=PIZZA_PARAMS,
        background_color=BG_PANEL,
        straight_line_color="#2E4057",
        straight_line_lw=1,
        last_circle_lw=1,
        last_circle_color="#2E4057",
        other_circle_ls="-.",
        other_circle_lw=0.5,
    )
    fig, _ = baker.make_pizza(
        values,
        figsize=(5, 5.5),
        color_blank_space="same",
        blank_alpha=0.12,
        kwargs_slices=dict(facecolor=ACCENT, edgecolor="#2E4057", zorder=2, linewidth=1, alpha=0.85),
        kwargs_params=dict(color=TEXT, fontsize=8, fontproperties=font_normal.prop, va="center"),
        kwargs_values=dict(
            color=TEXT, fontsize=8, fontproperties=font_normal.prop, zorder=3,
            bbox=dict(edgecolor="#2E4057", facecolor=ACCENT, boxstyle="round,pad=0.2", lw=1),
        ),
    )
    _dark_fig(fig)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f"<div style='padding:10px 0 14px'>"
        f"<span style='font-size:1.2rem;font-weight:700;color:{TEXT}'>Trilemma</span>"
        f"<br><span style='font-size:0.65rem;color:{TEXT_MUTED};letter-spacing:0.12em;"
        f"text-transform:uppercase'>Soccer Analytics</span></div>",
        unsafe_allow_html=True,
    )
    st.divider()

    # ── Player (outside form → triggers immediate re-run + updates season list)
    all_players = all_parity_players()
    default_player = (
        "Sergio Busquets i Burgos" if "Sergio Busquets i Burgos" in all_players
        else all_players[0]
    )
    selected_player = st.selectbox(
        "Player", all_players, index=all_players.index(default_player)
    )

    # ── Season + Condition inside form → only apply on button click ──────────
    with st.form("filters"):
        player_seasons = ["All Seasons"] + seasons_for_player(selected_player)
        selected_season = st.selectbox("Season", player_seasons, index=0)
        condition = st.radio("Match Condition", ["All", "Wins", "Non-Wins"])
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        st.form_submit_button("Apply Filters", use_container_width=True, type="primary")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN AREA
# ══════════════════════════════════════════════════════════════════════════════

# Compute stats outside sidebar so they're available to main area
pe = player_parity_events(selected_player, selected_season, condition)
n_matches = pe.select("match_id").unique().shape[0]
n_passes  = pe.filter(pl.col("type") == "Pass").shape[0]
n_shots   = pe.filter(pl.col("type") == "Shot").shape[0]
xg_total  = round(float(pe.filter(pl.col("type") == "Shot")["shot_statsbomb_xg"].sum() or 0), 2)

# ── Header ────────────────────────────────────────────────────────────────────
season_disp = selected_season if selected_season != "All Seasons" else "All Seasons"
st.markdown(
    f"<h2 style='margin-bottom:0'>Positional & Possession Structures</h2>"
    f"<p style='color:{TEXT_MUTED};font-size:0.80rem;margin:2px 0 0'>"
    f"xG-Parity Matches (|ΔxG| ≤ {XG_PARITY_THRESHOLD})"
    f"&nbsp;·&nbsp; {selected_player}"
    f"&nbsp;·&nbsp; {season_disp}"
    f"&nbsp;·&nbsp; {condition}"
    f"&nbsp;·&nbsp; {n_matches} matches</p>",
    unsafe_allow_html=True,
)
st.divider()

# ── Stat bar ──────────────────────────────────────────────────────────────────
s1, s2, s3, s4 = st.columns(4)
for col, label, val in [
    (s1, "Matches",  f"{n_matches}"),
    (s2, "Passes",   f"{n_passes:,}"),
    (s3, "Shots",    f"{n_shots}"),
    (s4, "xG",       f"{xg_total:.2f}"),
]:
    col.markdown(
        f"<div class='stat-card'>"
        f"<div class='stat-label'>{label}</div>"
        f"<div class='stat-value'>{val}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
player_passes = pe.filter(pl.col("type") == "Pass")

c_left, c_right = st.columns([1.15, 0.85])

with c_left:
    st.markdown("<div class='chart-label'>Pass End Locations — KDE</div>", unsafe_allow_html=True)
    fig_kde = plot_kde(player_passes)
    st.pyplot(fig_kde, use_container_width=True)
    plt.close(fig_kde)

with c_right:
    st.markdown("<div class='chart-label'>Percentile Rank</div>", unsafe_allow_html=True)
    fig_pz = plot_pizza()
    st.pyplot(fig_pz, use_container_width=True)
    plt.close(fig_pz)
