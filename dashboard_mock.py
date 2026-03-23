import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import FontManager, PyPizza
import polars as pl
import plotly.graph_objects as go
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
.block-container {{ padding-top: 1.2rem !important; padding-bottom: 0.5rem !important; }}
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
    "prog_dist_per_action", "central_progression_share", "wide_progression_share", "xg_diff",
]
METRIC_LABELS = [
    "Touch Share", "Touch Volume", "Progressive\nAction Share", "Progressive\nDistance Share",
    "Prog. Distance\nper Action", "Central\nProgression", "Wide\nProgression", "xG Differential",
]
POS_BINS_BY_GROUP = {
    "GK":  ["Goalkeeper"],
    "Def": ["Center Back", "Fullback"],
    "Mid": ["Defensive Midfield", "Central Midfield", "Attacking Midfield"],
    "Att": ["Wide Forward", "Striker"],
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

# ── Scatter data (module-level cache) ─────────────────────────────────────────
@st.cache_data
def build_scatter_data(year: str):
    ts = touch_share_s   if year == "All Years" else touch_share_s.filter(pl.col("season_name") == year)
    pa = prog_actions_s  if year == "All Years" else prog_actions_s.filter(pl.col("season_name") == year)
    return (
        ts.join(
            pa.select(["match_id", "team", "position_bin", "progressive_share"]),
            on=["match_id", "team", "position_bin"], how="left",
        )
        .filter(pl.col("position_bin").is_in(
            ["Defensive Midfield", "Central Midfield", "Attacking Midfield"]
        ))
        .group_by(["team", "outcome_binary"])
        .agg(
            pl.col("touch_share").mean().alias("touch_share"),
            pl.col("progressive_share").mean().alias("progressive_share"),
            pl.len().alias("n"),
        )
        .filter(pl.col("n") >= 5)
    ).to_pandas()

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
        .join(
            xg_parity.select(["match_id", "team", "xg_diff"]),
            on=["match_id", "team"], how="left",
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
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_overview, tab_team = st.tabs(["Overview", "Team View"])


# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:

    scatter_years = sorted(touch_share_s["season_name"].drop_nulls().unique().to_list())
    f1, _ = st.columns([1, 4])
    with f1:
        selected_scatter_year = st.selectbox("Season", ["All Years"] + scatter_years, key="scatter_year")

    all_mid    = build_scatter_data(selected_scatter_year)
    win_df     = all_mid[all_mid["outcome_binary"] == "Win"]
    nonwin_df  = all_mid[all_mid["outcome_binary"] == "Non-Win"]
    mean_touch = all_mid["touch_share"].mean()
    mean_prog  = all_mid["progressive_share"].mean()

    fig_scatter = go.Figure()
    fig_scatter.add_trace(go.Scatter(
        x=nonwin_df["touch_share"],
        y=nonwin_df["progressive_share"],
        mode="markers",
        name="Non-Win",
        marker=dict(color=BLUE, opacity=0.5, size=nonwin_df["n"] ** 0.55 * 3, line=dict(width=0)),
        customdata=nonwin_df[["team", "n"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Touch Share: %{x:.3f}<br>"
            "Progressive Share: %{y:.3f}<br>"
            "Matches: %{customdata[1]}<extra>Non-Win</extra>"
        ),
    ))
    fig_scatter.add_trace(go.Scatter(
        x=win_df["touch_share"],
        y=win_df["progressive_share"],
        mode="markers",
        name="Win",
        marker=dict(color=CORAL, opacity=0.5, size=win_df["n"] ** 0.55 * 3, line=dict(width=0)),
        customdata=win_df[["team", "n"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Touch Share: %{x:.3f}<br>"
            "Progressive Share: %{y:.3f}<br>"
            "Matches: %{customdata[1]}<extra>Win</extra>"
        ),
    ))
    fig_scatter.add_vline(x=mean_touch, line=dict(color=GREY, dash="dash", width=1))
    fig_scatter.add_hline(y=mean_prog,  line=dict(color=GREY, dash="dash", width=1))

    year_note = selected_scatter_year if selected_scatter_year != "All Years" else "All Seasons"
    fig_scatter.update_layout(
        title=dict(
            text=(
                "Midfield: Touch Share vs Progressive Action Share<br>"
                f"<sup>All teams · min 5 matches per outcome · dot size = sample size · dashed = global mean · {year_note}</sup>"
            ),
            font=dict(color=WHITE, size=15), x=0,
        ),
        xaxis=dict(
            title="Midfield Touch Share (avg per match)",
            color=GREY, gridcolor="#252525", zerolinecolor="#252525",
            title_font=dict(color=TEXT_MUTED, size=11),
        ),
        yaxis=dict(
            title="Midfield Progressive Action Share (avg per match)",
            color=GREY, gridcolor="#252525", zerolinecolor="#252525",
            title_font=dict(color=TEXT_MUTED, size=11),
        ),
        paper_bgcolor=BG_DARK, plot_bgcolor=BG_DARK, font=dict(color=TEXT),
        legend=dict(
            bgcolor=BG_PANEL, bordercolor="rgba(26,120,207,0.4)", borderwidth=1,
            font=dict(color=WHITE, size=11),
            x=0.01, y=0.99, xanchor="left", yanchor="top",
        ),
        margin=dict(t=75, l=65, r=25, b=60),
        height=570,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TEAM VIEW TAB
# ══════════════════════════════════════════════════════════════════════════════
with tab_team:

    # ── Filters ───────────────────────────────────────────────────────────────
    all_teams   = sorted(wing_vs_central_s["team"].unique().to_list())
    default_idx = all_teams.index("Barcelona") if "Barcelona" in all_teams else 0

    f1, f2, f3 = st.columns([1, 1, 3])
    with f1:
        selected_team = st.selectbox("Team", all_teams, index=default_idx)
    with f2:
        team_years = sorted(
            wing_vs_central_s
            .filter(pl.col("team") == selected_team)["season_name"]
            .drop_nulls().unique().to_list()
        )
        selected_year = st.selectbox("Season", ["All Years"] + team_years, key="team_year")

    year_label = selected_year if selected_year != "All Years" else "All Seasons"

    # ── Filter data ───────────────────────────────────────────────────────────
    wvc_filtered = wing_vs_central_s
    if selected_year != "All Years":
        wvc_filtered = wvc_filtered.filter(pl.col("season_name") == selected_year)

    # ── Stats for left cards ──────────────────────────────────────────────────
    n_matches = (
        wvc_filtered
        .filter(pl.col("team") == selected_team)["match_id"]
        .n_unique()
    )

    xg_filtered = xg_parity_s.filter(pl.col("team") == selected_team)
    if selected_year != "All Years":
        xg_filtered = xg_filtered.filter(pl.col("season_name") == selected_year)

    win_rate     = (xg_filtered["outcome"] == "Win").sum() / max(len(xg_filtered), 1) * 100
    avg_xg_for   = xg_filtered["team_xg"].mean() or 0.0
    avg_xg_ag    = xg_filtered["opp_xg"].mean()  or 0.0
    central_pct  = (
        wvc_filtered
        .filter(pl.col("team") == selected_team)["central_progression_share"]
        .mean() or 0.0
    ) * 100

    # ── Legend row ────────────────────────────────────────────────────────────
    leg_col, _ = st.columns([2, 3])
    with leg_col:
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

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Three-column layout: stat cards (left) | dumbbell | pizzas ────────────
    col_cards, col_dump, col_pizza = st.columns([0.38, 1.15, 1])

    # ── Dumbbell ──────────────────────────────────────────────────────────────
    league_agg = (
        wvc_filtered
        .group_by("position_bin")
        .agg(pl.col("central_progression_share").mean().alias("central"))
        .sort("central", descending=True)
    )
    order      = league_agg["position_bin"].to_list()
    league_avg = dict(zip(league_agg["position_bin"].to_list(), league_agg["central"].to_list()))

    team_agg = (
        wvc_filtered
        .filter(pl.col("team") == selected_team)
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

    def _card(label, value, val_style=""):
        return (
            f"<div class='stat-card' style='margin-bottom:8px'>"
            f"<div class='stat-label'>{label}</div>"
            f"<div class='stat-value' style='{val_style}'>{value}</div>"
            f"</div>"
        )

    with col_cards:
        st.markdown(
            _card("Positional Category", "—", "font-size:1.1rem") +
            _card("Matches", n_matches) +
            _card("Win Rate", f"{win_rate:.0f}%") +
            _card("Avg xG For", f"{avg_xg_for:.2f}") +
            _card("Avg xG Against", f"{avg_xg_ag:.2f}") +
            _card("Central Progression", f"{central_pct:.0f}%"),
            unsafe_allow_html=True,
        )

    with col_dump:
        fig_db, ax = plt.subplots(figsize=(7, 5.5), facecolor=BG_MAIN)
        ax.set_facecolor(BG_DARK)
        for i, pos in enumerate(order):
            lv = league_avg[pos]
            bw = team_win.get(pos)
            bn = team_nonwin.get(pos)
            if bw is not None and bn is not None:
                ax.plot([bw, bn], [i, i], color=WHITE, lw=1.2, alpha=0.4, zorder=2)
            ax.scatter(lv, i, color=GREY, s=65, zorder=3, marker="D")
            if bw is not None:
                ax.scatter(bw, i, color=CORAL, s=110, zorder=4, edgecolors=WHITE, linewidths=0.8)
            if bn is not None:
                ax.scatter(bn, i, color=BLUE, s=110, zorder=4, edgecolors=WHITE, linewidths=0.8)
        ax.axvline(0.5, color=GREY, lw=0.8, ls="--", alpha=0.5, zorder=1)
        ax.text(0.504, len(order) - 0.4, "50/50", color=GREY, fontsize=7,
                fontproperties=font_normal.prop)
        ax.set_yticks(range(len(order)))
        ax.set_yticklabels(order, color=WHITE, fontsize=9, fontproperties=font_normal.prop)
        ax.tick_params(axis="x", colors=GREY, labelsize=8)
        ax.set_xlim(0.2, 0.95)
        ax.set_xlabel("Central Progression Share  (0 = wide, 1 = central)",
                      color=TEXT_MUTED, fontsize=8, fontproperties=font_normal.prop, labelpad=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#2E323A")
        ax.set_title(
            "Central vs Wide Progression by Position",
            color=WHITE, fontsize=10, pad=10, fontproperties=font_bold.prop,
        )
        plt.tight_layout()
        st.pyplot(fig_db, use_container_width=True)
        plt.close(fig_db)

    # ── Single Pizza ──────────────────────────────────────────────────────────
    with col_pizza:
        grouped_grp, grouped_bin = build_pizza_aggs(selected_year)

        groups = list(POS_BINS_BY_GROUP.keys())
        selected_group = st.radio(
            "Position Group",
            groups,
            horizontal=True,
            key="pizza_group",
        )

        # rendered_height ∝ figsize_h/figsize_w × container_width
        # to match dumbbell (7×5.5 in col 1.15): target = (5.5/7)×(1.15/1.0) ≈ 0.90
        # → figsize (5.5, 5.0) gives aspect 0.909, close enough.
        fig_pz, ax_pz = plt.subplots(
            figsize=(5.5, 5.0),
            subplot_kw=dict(projection="polar"),
        )
        fig_pz.patch.set_facecolor(BG_MAIN)
        ax_pz.set_facecolor(BG_DARK)

        PyPizza(params=METRIC_LABELS, **PIZZA_KWARGS).make_pizza(
            get_pct_group(grouped_grp, selected_team, selected_group, "Non-Win"),
            compare_values=get_pct_group(grouped_grp, selected_team, selected_group, "Win"),
            ax=ax_pz,
            kwargs_slices=KW_NONWIN, kwargs_compare=KW_WIN,
            kwargs_params=KW_PARAMS, kwargs_values=KW_VALS, kwargs_compare_values=KW_CVALS,
        )
        fig_pz.suptitle(
            f"Percentile Rank vs All Teams — {selected_group}",
            fontproperties=font_bold.prop, fontsize=10, color=WHITE, y=0.98,
        )
        plt.tight_layout(rect=[0, 0, 1, 0.92])
        st.pyplot(fig_pz, use_container_width=True)
        plt.close(fig_pz)
