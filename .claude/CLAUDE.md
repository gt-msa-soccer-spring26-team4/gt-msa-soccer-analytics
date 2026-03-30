# GT MSA Soccer Analytics — Claude Context

## Project Overview
Georgia Tech MSA Spring 2026 capstone. The goal is an open-source pipeline that ingests StatsBomb public match event data and Polymarket prediction market data to produce interactive player/team analytics dashboards.

**Primary notebook for visualization work:** `eda/experiments/mplsoccer_viz.ipynb`

---

## What Has Been Built in `mplsoccer_viz.ipynb`

### 1. Basic Pitch Layout
- Horizontal pitch (`Pitch`) with grass color, white lines, and stripes
- Vertical pitch (`VerticalPitch`) with same styling
- Uses `mplsoccer` library

### 2. Hexbin and KDE Plot (Action Distribution)
- **Match:** Barcelona vs Deportivo Alavés — `match_id = 15946`
- **Player:** Sergio Busquets — `player_id = 5203`
- **KDE pass end-location map** — `VerticalPitch` with `pitch.kdeplot()` on `pass_end_location_x/y`, `fill=True`, `levels=100`, `Reds` cmap
- **Hexbin pass end-location map** — `pitch.hexbin()` on `pass_end_location_x/y`, custom flamingo colormap (`#e3aca7` → `#c03a1d`), `gridsize=(8,8)`
- Both use `pitch.grid()` layout with title/endnote axes

### 3. Pizza Plot (Single Player Percentile Radar) — uses fake data
- **Parameters:** Touches, Positional Touch Share, Passes, Forward Pass Progression, xA, Total Carry Distance, Progressive Carry Distance, Carries into Final Third, Goal Creating Actions, xT
- Uses `mplsoccer.PyPizza` with `lightcoral` fill, `#000000` text
- Title: "Sergio Busquets - FC Barcelona", subtitle: "Percentile Rank Among Midfielders in xG-Parity Matches"
- Loads Google Fonts (Roboto, RobotoSlab) via `mplsoccer.FontManager`

### 4. Comparison Pizza Plot (Wins vs Non-Wins) — uses fake data
- Same parameters as above, two value sets: `values_wins` and `values_nonwins`
- Blue (`#1A78CF`) for non-wins, `lightcoral` for wins
- Uses `highlight_text.fig_text` for colored subtitle annotations
- Background: `#EBEBE9`, dark straight lines

### 5. Positional Group Pizza Plots — Barcelona, real data
Three wide figures (one per position unit) inserted between the Busquets pizzas and the animation section. Each figure has:
- **Left panel**: group-level comparison pizza (all positions in the unit combined)
- **Bold vertical separator**: `ax.axvline(0.5, linewidth=8, color="#111111")` on a thin GridSpec column
- **Right panels**: one comparison pizza per individual `position_bin` in the unit

Layout uses `matplotlib.gridspec.GridSpec` with `width_ratios=[10, 0.5, 10, 10, ...]`. Each pizza is drawn into a subplot axes via `PyPizza(...).make_pizza(..., ax=ax)`.

**Position units and bins:**
- `GK + Def`: Goalkeeper, Center Back, Fullback → 4 pizzas total (1 group + 3)
- `Mid`: Defensive Midfield, Central Midfield, Attacking Midfield → 4 pizzas total
- `Att`: Wide Forward, Striker → 3 pizzas total

**8 metrics (percentile-ranked vs all teams, per slice + outcome_binary):**

| # | Label | Source | Derivation |
|---|---|---|---|
| 1 | Touch Share | `positional_touch_share.touch_share` | direct |
| 2 | Touch Volume | `positional_touch_share.touches` | direct |
| 3 | Progressive Action Share | `positional_progressive_actions_share.progressive_share` | direct |
| 4 | Progressive Distance Share | `positional_progressive_distance_share.progressive_distance_share` | direct |
| 5 | Prog. Distance per Action | derived | `progressive_distance / progressive_actions` |
| 6 | Central Progression | `positional_wing_vs_central_progression_share.central_progression_share` | direct |
| 7 | Wide Progression | `positional_wing_vs_central_progression_share.wide_progression_share` | direct |
| 8 | xG Differential | `xg_parity_matches.xg_diff` | team-level, joined on match_id + team |

**Key implementation notes:**
- All 5 CSVs joined into a single `base` table; `pos_group` column maps 8 bins to 3 units
- Two separate aggregations: `grouped_grp` (team + pos_group + outcome_binary) and `grouped_bin` (team + position_bin + outcome_binary)
- `get_pct_group()` and `get_pct_bin()` both call `_rank()` which percentile-ranks one team's mean against all teams in the same filter slice
- Wins = coral (`lightcoral`), Non-Wins = blue (`#1A78CF`); figure-level `Patch` legend top-right
- `fig.suptitle(..., y=1.02)` used for title since `fig_text` is figure-relative and conflicts with GridSpec layout

### 6. Midfield Impact Figures — real data, dark theme

Two figures inserted after the positional group pizzas. Both use `#1B1B1B` dark background.

**Figure 1: Dumbbell Plot — Central vs Wide Progression by Position**
- All 8 position bins on Y-axis, sorted by league average centrality (most central at top)
- For each position: grey diamond = league average, coral circle = Barcelona Win, blue circle = Barcelona Non-Win
- White connector line between Barcelona Win and Non-Win dots
- X-axis: `central_progression_share` (0 = all wide, 1 = all central); dashed line at 0.5 (even split)
- Source: `positional_wing_vs_central_progression_share.csv`, Barcelona filtered + full league mean
- Key insight: Barcelona is substantially more central than league average at most positions; in wins, wide forwards and strikers spread wider

**Figure 2: Scatter — Touch Share × Progressive Action Share (Midfield)**
- All teams with ≥5 matches per outcome, aggregated to mean per team+outcome_binary
- X = `touch_share`, Y = `progressive_share`, dot size = `n * 3` (sample size)
- Wins in `lightcoral`, Non-Wins in `#1A78CF`, `alpha=0.3` for background teams; Barcelona at `s=250`, `zorder=5`, white edge + bold label
- Dashed grey reference lines at global mean of both axes (visual quadrant split)

### 7. Animation (Labeled "Probably Won't Need") — commented out
- Filters Busquets events to first 10 minutes (`minute <= 9`)
- Animates player position (blue dot) and ball (white dot) frame-by-frame across passes and carries
- Uses `matplotlib.animation.FuncAnimation` + `IPython.display.HTML`
- `mpl.rcParams['animation.embed_limit'] = 75.0` set to handle large sequences
- Save path: `experiments/viz_video.gif` — currently commented out

---

## Processed Data Schema

All visualization work draws from `data/processed/`. These CSVs contain pre-aggregated, match-level metrics grouped by team and positional group.

---

### `positional_touch_share.csv` — 9,039 rows × 8 columns

Touch volume and share of total team touches, broken down by position group per match.

| Column | Type | Description |
|---|---|---|
| `match_id` | Int64 | Match identifier |
| `team` | String | Team name |
| `position_bin` | String | Positional group (see shared dimensions below) |
| `touches` | Int64 | Total touches by this position group |
| `team_touches` | Int64 | Total team touches in the match |
| `touch_share` | Float64 | `touches / team_touches` |
| `outcome` | String | Win / Draw / Loss |
| `outcome_binary` | String | Win / Non-Win |

---

### `positional_progressive_actions_share.csv` — 9,014 rows × 8 columns

Count of progressive actions (passes/carries moving the ball toward goal) and their share of the team total, by position group per match.

| Column | Type | Description |
|---|---|---|
| `match_id` | Int64 | Match identifier |
| `team` | String | Team name |
| `position_bin` | String | Positional group |
| `progressive_actions` | Int64 | Count of progressive actions by this position group |
| `team_progressive_actions` | Int64 | Total team progressive actions in the match |
| `progressive_share` | Float64 | `progressive_actions / team_progressive_actions` |
| `outcome` | String | Win / Draw / Loss |
| `outcome_binary` | String | Win / Non-Win |

---

### `positional_progressive_distance_share.csv` — 9,014 rows × 8 columns

Total progressive distance (meters carried/passed toward goal) and positional share, per match.

| Column | Type | Description |
|---|---|---|
| `match_id` | Int64 | Match identifier |
| `team` | String | Team name |
| `position_bin` | String | Positional group |
| `progressive_distance` | Float64 | Total progressive distance by this position group |
| `team_progressive_distance` | Float64 | Total team progressive distance in the match |
| `progressive_distance_share` | Float64 | `progressive_distance / team_progressive_distance` |
| `outcome` | String | Win / Draw / Loss |
| `outcome_binary` | String | Win / Non-Win |

---

### `positional_wing_vs_central_progression_share.csv` — 9,014 rows × 7 columns

For each position group per match, what fraction of progressive actions went through the center vs. wide channels.

| Column | Type | Description |
|---|---|---|
| `match_id` | Int64 | Match identifier |
| `team` | String | Team name |
| `position_bin` | String | Positional group |
| `central_progression_share` | Float64 | Share of this group's progressive actions through central channels |
| `wide_progression_share` | Float64 | Share through wide channels (`1 - central_progression_share`) |
| `outcome` | String | Win / Draw / Loss |
| `outcome_binary` | String | Win / Non-Win |

---

### `xg_parity_matches.csv` — 1,302 rows × 8 columns

Match-level xG summary. Both teams appear as separate rows per match. Useful for identifying xG-parity matches (close games) and comparing performance vs. outcome.

| Column | Type | Description |
|---|---|---|
| `match_id` | Int64 | Match identifier |
| `team` | String | Team name |
| `opponent` | String | Opponent name |
| `team_xg` | Float64 | Total xG generated by the team |
| `opp_xg` | Float64 | Total xG generated by the opponent |
| `xg_diff` | Float64 | `abs(team_xg - opp_xg)` — closeness of the match |
| `shots` | Int64 | Total shots by the team |
| `outcome` | String | Win / Draw / Loss |

---

### `team_level_metrics.csv` — 1,302 rows × 7 columns

Team-level tactical metrics per match. One row per team per match. Captures overall progression style and central midfield involvement.

| Column | Type | Description |
|---|---|---|
| `match_id` | Int64 | Match identifier |
| `team` | String | Team name |
| `outcome` | String | Win / Draw / Loss |
| `wide_progression_share` | Float64 | Share of progressive actions through wide channels |
| `build_up_share` | Float64 | Share of progressive actions in the build-up phase |
| `max_progression_share` | Float64 | Largest single positional group's share of progressive actions (dominant position) |
| `central_midfield_touch_share` | Float64 | Central midfield's share of total team touches |

Note: joins to positional CSVs on `match_id` + `team`; no `outcome_binary` column — derive as `Win` vs `Non-Win` if needed.

---

## Shared Dimension Values

**`position_bin`** (8 groups, consistent across all positional CSVs):
- `Goalkeeper`
- `Center Back`
- `Fullback`
- `Defensive Midfield`
- `Central Midfield`
- `Attacking Midfield`
- `Wide Forward`
- `Striker`

**`outcome`**: `Win`, `Draw`, `Loss`

**`outcome_binary`**: `Win`, `Non-Win`

---

## Key Notes for Building Further Figures

### Joining the CSVs
All positional files share `match_id`, `team`, `position_bin`, `outcome`, and `outcome_binary` — they join directly on those keys. `xg_parity_matches` and `team_level_metrics` join on `match_id` + `team`.

### Suggested Next Figures
1. **Positional touch share by outcome** — grouped bar or violin, `touch_share` by `position_bin`, split by `outcome_binary`
2. **Progressive action share by outcome** — same structure with `progressive_share`
3. **Wide vs. central progression by position** — stacked bar of `central_progression_share` vs `wide_progression_share` per `position_bin`, colored by `outcome_binary`
4. **xG parity scatter** — `team_xg` vs `opp_xg`, colored by `outcome`, annotated with `xg_diff`
5. **Update Busquets pizza to real data** — replace fake `values` / `values_wins` / `values_nonwins` lists using the same percentile pipeline already built for the positional group plots

---

## Streamlit Dashboard (`dashboard_mock.py`)

### App Title
**"Positional Level Impact in xG-Parity Matches"**

No sidebar. Dark theme matching the notebook (`BG_MAIN = "#0E1117"`, `BG_DARK = "#1B1B1B"`).

### Layout: Two Tabs

#### Tab 1 — Overview
Single full-width chart: **Scatter — Midfield Touch Share × Progressive Action Share**

- Mirrors Figure 2 from `mplsoccer_viz.ipynb` but with no specific team highlighted
- All teams rendered semi-transparent (`alpha=0.3`), wins in coral, non-wins in blue
- Dot size scales with sample size (`n * 3`); teams with < 5 matches per outcome excluded
- Dashed grey reference lines at global means of both axes
- Data sources: `positional_touch_share.csv` joined with `positional_progressive_actions_share.csv` on `[match_id, team, position_bin]`, filtered to midfield position bins

#### Tab 2 — Team View
Top-line filter row (two selectboxes, left-aligned) + full-width dumbbell chart:

**Filters:**
- `Team` — dropdown of all teams in `positional_wing_vs_central_progression_share.csv`; defaults to "Barcelona"
- `Year` — dropdown of all seasons (joined from `matches.parquet` via `match_id`); first option is "All Years"

**Chart: Dumbbell — Central vs Wide Progression by Position**
- Mirrors Figure 1 from `mplsoccer_viz.ipynb` but parameterized by selected team and year
- Y-axis: all 8 position bins sorted by league average centrality (most central at top)
- Grey diamond = league average; coral circle = selected team Win; blue circle = selected team Non-Win
- White connector line between Win and Non-Win dots per position
- X-axis: `central_progression_share` (0 = all wide, 1 = all central); dashed 50/50 line
- Legend labels use selected team name dynamically; title includes team + year

### Data Loading
- `positional_touch_share.csv`, `positional_progressive_actions_share.csv`, `positional_wing_vs_central_progression_share.csv` loaded from `data/processed/`
- `matches.parquet` loaded from `data/Statsbomb/` — joined on `match_id` to add `season_name` for the year filter
- All loads are `@st.cache_data` decorated; fonts loaded with `@st.cache_resource`
