# Georgia Tech MSA Spring 2026 Practicum - Final Report
## Team 4: Winning Without an xG Advantage

**Authors:** Alexander Avramov, Noah Boonin, Thomas LaRock  
**Track:** Soccer Analytics Dashboard  
**Date:** April 2026

---

## EXECUTIVE SUMMARY (write last)
- Problem: 38% of matches have equal xG, but 35% still produce a winner — what explains this?
- Approach: Analyzed 651 xG-parity matches using clustering on positional structure
- Key findings: [3-5 bullets with numbers]
- Deliverable: Interactive dashboard for archetype exploration
- Impact: Enables tactical preparation when xG can't separate teams

---

## 1. INTRODUCTION & MOTIVATION (2 pages)

### 1.1 Background
- xG dominates modern soccer analytics
- But xG is incomplete when chance quality is equal

### 1.2 The xG-Parity Phenomenon
- 38% of matches: |ΔxG| ≤ 0.3
- 30% end in draws (vs 23% overall)
- Yet 35% produce a winner
- Average team xG: 1.14

### 1.3 Hypothesis
- Positional structure may explain outcomes when xG can't
- Winners allocate possession differently than non-winners

### 1.4 Project Goals
1. Identify structural differences in xG-parity matches
2. Develop archetype taxonomy
3. Build interactive dashboard
4. Validate with user testing

---

## 2. PROBLEM DEFINITION & RESEARCH QUESTION (2 pages)

### 2.1 The Gap
Current tools (FBref, Understat, StatsBomb) provide:
- xG values and shot maps
- Possession statistics

Current tools lack:
- xG-parity identification
- Positional structure analysis
- Tactical archetypes
- Interactive exploration

### 2.2 Research Question
**Do winning teams exhibit systematically different positional structures than non-winning teams in xG-parity matches?**

Sub-questions:
1. Touch distribution differences?
2. Progressive movement differences?
3. Distinct archetypes?
4. Archetype-outcome correlations?

### 2.3 Success Criteria
- ≥3 positions show p<0.05 touch share differences
- Silhouette score >0.4
- Cluster stability >80%
- Archetype-outcome χ² p<0.01
- User testing: ≥80% task success, ≥7/10 satisfaction

### 2.4 Scope & Limitations
**In scope:** xG-parity matches, clustering, dashboard, user testing  
**Out of scope:** Real-time prediction, individual players, causation  
**Limitations:** Barcelona-heavy data, reverse causality threat, 0.3 threshold choice

---

## 3. LITERATURE REVIEW (2-3 pages)

### 3.1 xG in Soccer Analytics

Expected goals (xG) has become the dominant metric in soccer analytics for evaluating team performance and explaining match outcomes (Mead et al., 2023; Rathke, 2017). The metric quantifies the probability that a given shot will result in a goal based on features such as shot location, angle, defensive pressure, and assist type.

**Foundational Work:**
Rathke (2017) provided one of the first comprehensive examinations of xG as a shot efficiency metric, demonstrating its superiority over traditional statistics in predicting team performance. More recent work by Mead et al. (2023) showed that xG models using machine learning techniques (logistic regression, random forest, XGBoost) achieve log-loss scores competitive with industry standards, with distance and angle being the most influential features.

**Industry Adoption:**
xG is now widely used by professional clubs for performance analysis, media outlets for match commentary, and betting markets for odds calculation (Green, 2012). Platforms like FBref, Understat, and StatsBomb have made xG accessible to the broader analytics community.

Recent work by Tahir et al. (2026) extended xG applications to season-level predictions, developing an inference-based probabilistic framework that converts shot-level event data into simulations of league points, rankings, and outcome probabilities. Applied to Leicester City's historic 2015/16 Premier League title win (5000-1 odds), their model correctly identified top-four contenders and relegation candidates while explaining variance in final standings. Their mid-season analysis showed Leicester ranking among the top teams by xG metrics (16.7% title probability), suggesting their success was unlikely but not entirely detached from underlying performance. This work demonstrates xG's value as a probabilistic baseline for identifying when teams significantly outperform or underperform their expected results.

**Known Limitations:**
Several studies have acknowledged xG's limitations:
- Does not capture buildup play or possession quality (Fernández et al., 2021)
- Treats all shots independently with no sequential context (Anzer & Bauer, 2021)
- Cannot explain outcomes when chance quality is equal between opponents
- Focuses exclusively on shooting actions, covering only a small subset of the game

This final limitation motivates our focus on the xG-parity regime, where traditional xG-based evaluation offers limited explanatory power. Recent work by Malikov and Kim (2024) has addressed some of these limitations by proposing a dual prediction model that combines both expected goals (xG) and actual goals (aG) to provide more comprehensive player performance assessment. Their approach demonstrates that incorporating both metrics improves prediction accuracy and offers deeper insights into player efficiency and finishing ability.

Additionally, Bandara et al. (2024) demonstrated that incorporating event sequence information preceding shots significantly improves xG model performance (ROC-AUC: 0.833). Using Random Forest models with StatsBomb data, they found that including information from the shot event plus two preceding events achieved the best performance. Their work revealed that opportunities built from the sides of the 18-yard box and shots following successful passes to the far post improve scoring probabilities. This approach of considering temporal sequences challenges the notion that goal scoring is primarily random and highlights the importance of tactical buildup patterns.

### 3.2 Tactical Analysis

**Positional Play and Structure:**
Research on tactical structure in soccer has increasingly focused on spatial patterns and formation analysis. Memmert et al. (2017) provided a comprehensive review of tactical performance analysis using position data, noting the shift from notational analysis to spatiotemporal approaches. Clemente et al. (2016) used network analysis to examine passing patterns and team connectivity, demonstrating how positional relationships affect offensive success.

**Possession-Based Metrics:**
Beyond xG, researchers have developed metrics to quantify possession quality and territorial control. Fernández et al. (2021) introduced Expected Possession Value (EPV), which estimates the probability of scoring from any possession state, not just shots. This framework explicitly models buildup play, addressing a key limitation of xG.

**Formation and Style Analysis:**
Recent work by Romero Clavijo et al. (2024) used cluster analysis to identify distinct attacking and defensive styles, finding that spatial variables (positions and displacements) contributed most to pattern separation. This aligns with our approach of using positional touch shares and progressive movements as key features.

**Gap in Current Research:**
While existing research analyzes possession patterns across all matches (Link et al., 2016; Clemente et al., 2016), **no published work specifically examines positional structure in xG-parity matches** — the subset where tactical structure may matter most. Our study addresses this gap by isolating matches where chance quality is equal and investigating whether positional differences explain outcomes.

### 3.3 Clustering in Sports

**Applications in Soccer:**
Clustering has been successfully applied to identify tactical patterns in soccer. Yamamoto et al. (2019) developed a clustering algorithm for formations using Delaunay triangulation, successfully identifying standard formations (4-4-2, 4-3-3, etc.) and their variations from tracking data. Shaw and Glickman (2019) used hierarchical clustering to detect 20 distinct formation types and track tactical changes during matches.

**Player Style Classification:**
Beyond formations, clustering has been used to classify player roles and styles. Bialkowski et al. (2014) analyzed large-scale spatiotemporal data to categorize playing styles across teams. Michalczyk (2019) applied clustering to Premier League build-up play patterns, revealing team-specific passing preferences. Tewachew (2025) used per-90 performance stats to cluster players by tactical role (pressing forward, playmaker, destroyer) rather than positional labels.

**Methodological Approaches:**
Common clustering algorithms in soccer analytics include:
- **K-means:** Fast, interpretable, assumes spherical clusters (Yamamoto et al., 2019)
- **Hierarchical:** Reveals cluster hierarchy, no need to pre-specify k (Shaw & Glickman, 2019)
- **DBSCAN:** Handles non-spherical clusters, robust to outliers (Fernando et al., 2015)

**Applications in Other Sports:**
Clustering has proven valuable in basketball (player role identification), baseball (pitcher repertoire classification), and hockey (zone entry pattern detection), demonstrating its generalizability across team sports.

**Transfer to Our Study:**
While clustering is common in soccer formation and player analysis, **applications to match-level positional structure** in specific competitive regimes (like xG-parity) remain underdeveloped. Our approach extends existing methods by clustering team-level possession patterns rather than formations or player types.

### 3.4 Existing Tools

**FBref (Sports Reference LLC):**
Provides comprehensive match statistics including xG values, shot maps, and basic possession metrics. Offers historical data across multiple competitions but lacks advanced filtering for competitive regimes like xG-parity.

**Understat:**
Focuses on xG analytics with timeline visualizations, shot quality assessments, and rolling averages. Provides team and player-level xG tracking but does not support archetype identification or tactical pattern analysis.

**StatsBomb IQ:**
Offers event-level data access including defensive actions, passing networks, and spatial analysis tools (StatsBomb, 2024). Requires technical expertise (Python/R) to analyze data. The platform provides granular event data but no pre-built framework for identifying positional archetypes or xG-parity subsets.

**Data Access:**
StatsBomb's Open Data repository (StatsBomb, 2024) has democratized access to high-quality event data, covering 3,464 matches across 18 competitions. The data includes 12.2M events with spatial coordinates, player positions, and xG values for all shots. Documentation by Carrasquilla (2026) provides comprehensive guides for working with the dataset.

**Gap Addressed by This Project:**
No existing tool provides:
1. Automatic identification of xG-parity matches as a distinct analytical regime
2. Positional archetype classification based on possession structure
3. Interactive archetype exploration for non-technical users (coaches, scouts)
4. Match-level examples for tactical video review linked to archetypes

Our dashboard fills this gap by making positional pattern analysis accessible to practitioners without requiring coding expertise.

### 3.5 Our Contribution
- Novel framing (xG-parity regime)
- Archetype taxonomy
- Accessible interactive tool

---

## 4. DATA & METHODOLOGY (3-4 pages)

### 4.1 Data Sources
- StatsBomb Open Data: 3,464 matches, 12.2M events
- 18 competitions, 25 seasons
- [Competition coverage table]

### 4.2 Data Processing
**Step 1:** Match-level xG = Σ(shot xG)  
**Step 2:** xG-parity = |ΔxG| ≤ 0.3 → 651 matches  
**Step 3:** Position mapping → 8 groups (GK, CB, FB, DM, CM, AM, WF, ST)  
**Step 4:** Touch events = passes + receipts + carries + dribbles + shots  
**Step 5:** Normalize: touch_share = position_touches / team_touches

[Threshold sensitivity: test 0.2, 0.3, 0.5]

### 4.3 Feature Engineering (Weeks 8-10)
1. **Progression-weighted touch shares** [formula]
2. **Zone-adjusted possession** (defensive/middle/attacking thirds)
3. **Composite control score** (position + movement + security)
4. **Attacking index** (sterile vs attacking possession)

### 4.4 Data Quality
- 99.2% touch events have positions
- 100% shots have xG
- All team-match touch shares sum to 1.0±0.001

### 4.5 Innovation
1. xG-parity as analytical lens (novel framing)
2. Archetype taxonomy (beyond binary win/loss)
3. Interactive non-technical tool (accessible)

---

## 5. EXPLORATORY DATA ANALYSIS (4-5 pages)

### 5.1 Dataset Overview
- 651 matches (37.6% of dataset)
- [Competition breakdown table]
- [Temporal distribution chart]

### 5.2 xG Distribution
- [Histogram: all matches vs xG-parity]
- Mean xG in parity: 1.14

### 5.3 Outcome Distribution
| Outcome | All | xG-Parity | Diff |
|---------|-----|-----------|------|
| Win | 38.5% | 35.1% | -3.4pp |
| Draw | 23.1% | 29.8% | **+6.7pp** |
| Loss | 38.4% | 35.1% | -3.3pp |

Confirms: equal xG suppresses wins, increases draws

### 5.4 Touch Share Analysis
**Finding:** Winners shift forward (+2.67pp advanced, -1.61pp defensive)

| Position | Win | Non-Win | Diff |
|----------|-----|---------|------|
| AM | 16.8% | 15.3% | +1.50% |
| WF | 12.1% | 11.3% | +0.85% |
| ST | 9.3% | 8.5% | +0.78% |
| CB | 14.2% | 15.2% | -0.98% |
| DM | 5.8% | 6.8% | -1.04% |

[Statistical tests: Mann-Whitney U for each position]

### 5.5 Progressive Carries
**Finding:** Winners carry forward more aggressively

| Position | Win | Non-Win | Diff |
|----------|-----|---------|------|
| ST | 3.91 | 3.52 | +0.39 yds |
| AM | 3.67 | 3.36 | +0.31 |
| CB | 1.76 | 2.03 | -0.27 |

[Bar chart showing differences]

### 5.6 Pass Locations
**Finding:** Wins show more spatial variance in attacking positions

- 8-panel heatmap (top passer per position)
- Wins: spread across attacking third
- Non-wins: clustered, predictable
- Note: All Barcelona players (dataset limitation)

### 5.7 Summary
Three consistent patterns:
1. Touch allocation (where)
2. Ball movement (how)
3. Spatial variance (spread)

---

## 6. CLUSTERING ANALYSIS (4-5 pages)

### 6.1 Feature Engineering Results (from 4.3)
- Document final formulas
- Distribution by outcome
- Correlation with winning

### 6.2 Feature Selection
- Initial: [N] features
- Correlation analysis → remove redundant
- Final: [M] features

### 6.3 Clustering Method
**Algorithms tested:** K-means, Hierarchical, DBSCAN  
**Evaluation:** Silhouette, Davies-Bouldin, interpretability  
**Final choice:** [Algorithm] with k=[N] clusters

[Elbow plot, silhouette analysis]

### 6.4 Validation
- Silhouette score: [value]
- Bootstrap stability: [X]% iterations stable
- Per-cluster silhouette scores

### 6.5 Archetypes Identified
**For each of [k] clusters:**

#### Archetype 1: [Name]
- Size: [N] observations ([%])
- Win rate: [X]% (vs 35.1% overall)
- Defining features: [top 3 with values]
- Tactical interpretation: [2-3 sentences]
- Representative matches: [3-5 examples]
- Common teams: [list]

[Repeat for all k archetypes]

### 6.6 Archetype-Outcome Relationship

| Archetype | Win% | Draw% | Loss% | N |
|-----------|------|-------|-------|---|
| [Name 1] | [%] | [%] | [%] | [N] |
| [Name 2] | [%] | [%] | [%] | [N] |

**Chi-square test:** χ²=[X], p=[Y]  
**Effect size:** [max-min] = [X]pp difference

---

## 7. RESULTS & VALIDATION (3-4 pages)

### 7.1 Key Findings (4-6 bullets)
1. [Primary finding with specific numbers and p-value]
2. [Secondary finding]
3. [Tertiary finding]
...

### 7.2 Literature Comparison
- Our findings vs prior work on xG, positioning, archetypes
- What's novel, what's confirmatory

### 7.3 Statistical Summary
| Test | Result | Interpretation |
|------|--------|----------------|
| Touch share diffs | [N]/8 p<0.05 | Significant |
| Archetype-outcome | χ²=[X], p<0.01 | Associated |
| Cluster stability | [X]% stable | Robust |

### 7.4 Sensitivity Analysis
- Different algorithms: [results]
- Different features: [results]
- Different thresholds (0.2, 0.5): [results]

### 7.5 User Testing (N=6-10)

**Tasks:**
1. Identify team archetype (<2 min)
2. Compare teams (<3 min)
3. Find match examples (<4 min)

**Results:**
- Task success: [X]% (target: 80%)
- Avg time: [X] min (target: <3)
- Satisfaction: [X]/10 (target: ≥7)

**Feature ranking:**
1. [Most valued feature]
2. [2nd]
...

**Feedback themes:**
- Add more airlines → Add more leagues/years
- Improve GUI
- Direct booking links → Export/share functions

**Changes made:** [list]

---

## 8. INTERACTIVE DASHBOARD (2-3 pages)

### 8.1 Overview
- URL: [deployed link]
- Purpose: Explore archetypes without coding

### 8.2 Use Cases
1. **Pre-match scouting:** Identify opponent's typical archetype
2. **Self-assessment:** Compare own team to winning patterns
3. **Historical research:** Cross-competition/season patterns

### 8.3 Features
- Filter: competition, season, team, archetype
- Visualizations: side-by-side profiles, pitch heatmaps
- Match browser: representative examples per archetype
- Comparison tool: two teams or archetypes
- Export: CSV download

### 8.4 Tech Stack
- Backend: Python (Flask/FastAPI)
- Frontend: React + D3.js
- Database: [PostgreSQL/SQLite]
- Hosting: [AWS/GCP/Heroku]
- Architecture: [diagram]

### 8.5 User Guide
[Screenshots with captions]
1. Getting started
2. Filtering data
3. Comparing teams
4. Exploring matches

---

## 9. CONCLUSIONS & FUTURE WORK (2 pages)

### 9.1 Summary
- Identified [k] archetypes with [X]pp win rate spread
- Statistical significance: [summary]
- Dashboard validated: [X]/10 satisfaction

### 9.2 Practical Implications
- Coaches: Pre-match prep, tactical adjustments
- Analysts: Complement to xG analysis
- Researchers: Novel analytical framework

### 9.3 Limitations
- Reverse causality threat
- Barcelona-heavy sample
- Historical data (2015-2021)
- Threshold sensitivity

### 9.4 Future Work
**Methodological:**
- Causal inference (propensity matching)
- Temporal evolution analysis
- Player-level decomposition
- Real-time integration

**Dashboard:**
- Video integration
- Predictive mode
- Mobile app
- Multi-match aggregation

**Research:**
- Non-parity matches
- Other outcomes (goals, possession%)
- Transfer to other sports

### 9.5 Final Remarks
When xG is equal, positional structure matters. Winners push forward, non-winners circulate deeper. Dashboard makes this actionable.

---

## 10. TEAM CONTRIBUTIONS

**Alexander Avramov:**
- [Primary]: Feature engineering, clustering
- [Support]: EDA visualization

**Noah Boonin:**
- [Primary]: Dashboard frontend
- [Support]: Data pipeline

**Thomas LaRock:**
- [Primary]: Statistical analysis, report writing
- [Support]: Dashboard backend

---

## 11. REFERENCES

### Expected Goals (xG) Literature

Tahir, S. B. U. D., et al. (2026). Leicester's tale: Another perspective on the EPL 2015/16 through expected goals (xG) modelling. *arXiv preprint*. arXiv:2602.15673. https://arxiv.org/abs/2602.15673

Bandara, I., Shelyag, S., Rajasegarar, S., Dwyer, D., Kim, E.-j., & Angelova, M. (2024). Predicting goal probabilities with improved xG models using event sequences in association football. *PLOS ONE*, 19(10), e0312278. https://doi.org/10.1371/journal.pone.0312278

Malikov, D., & Kim, J. (2024). Beyond xG: A dual prediction model for analyzing player performance through expected and actual goals in European soccer leagues. *Applied Sciences*, 14(22), 10390. https://doi.org/10.3390/app142210390

Mead, J., O'Hare, A., & McMenemy, P. (2023). Expected goals in football: Improving model performance and demonstrating value. *PLOS ONE*, 18(4), e0282295. https://doi.org/10.1371/journal.pone.0282295

Rathke, A. (2017). An examination of expected goals and shot efficiency in soccer. *Journal of Human Sport and Exercise*, 12(2), 514-529.

Green, S. (2012). Assessing the performance of Premier League goalscorers. *StatsBomb Blog*. https://statsbomb.com/articles/soccer/

Anzer, G., & Bauer, P. (2021). A goal scoring probability model for shots based on synchronized positional and event data in football (soccer). *Frontiers in Sports and Active Living*, 3, 624475.

Robberechts, P., & Davis, J. (2020). How data availability affects the ability to learn good xG models. In *International Workshop on Machine Learning and Data Mining for Sports Analytics* (pp. 17-27). Springer.

### Tactical Analysis & Positional Play

Romero Clavijo, F. A., Drews, R., Denardi, R. A., Travassos, B., & Corrêa, U. C. (2024). Identification of football teams styles of play by cluster analysis. *International Journal of Performance Analysis in Sport*, 24(1), 123-142. https://doi.org/10.1177/17479541231186796

Memmert, D., Lemmink, K. A., & Sampaio, J. (2017). Current approaches to tactical performance analyses in soccer using position data. *Sports Medicine*, 47(1), 1-10.

Clemente, F. M., Martins, F. M. L., & Mendes, R. S. (2016). Analysis of scored and conceded goals by a football team throughout a season: A network analysis. *Kinesiology*, 48(1), 103-114.

Fernández, J., Bornn, L., & Cervone, D. (2021). A framework for the fine-grained evaluation of the instantaneous expected value of soccer possessions. *Machine Learning*, 110(6), 1389-1427.

### Clustering Methods in Sports Analytics

Yamamoto, Y., Yokoyama, K., Okada, K., Nagahara, M., & Shimizu, Y. (2019). Clustering algorithm for formations in football games. *Scientific Reports*, 9, 13172. https://doi.org/10.1038/s41598-019-48623-1

Shaw, L., & Glickman, M. E. (2019). Dynamic analysis of team strategy in professional football. *Barça Sports Analytics Summit*. https://www.researchgate.net/publication/330778714

Bialkowski, A., Lucey, P., Carr, P., Yue, Y., Sridharan, S., & Matthews, I. (2014). Large-scale analysis of soccer matches using spatiotemporal tracking data. In *2014 IEEE International Conference on Data Mining* (pp. 725-730). IEEE.

Fernando, T., Wei, X., Fookes, C., Sridharan, S., & Lucey, P. (2015). Discovering methods of scoring in soccer using tracking data. In *Large-Scale Sports Analytics Workshop* at KDD 2015.

### Big Data & Machine Learning in Soccer

Link, D., Lang, S., & Seidenschwarz, P. (2016). Big data and tactical analysis in elite soccer: Future challenges and opportunities for sports science. *SpringerPlus*, 5(1), 1410. https://doi.org/10.1186/s40064-016-3108-2

Tewachew, Y. (2025). Clustering soccer players based on match activity. *INST414: Data Science Techniques*. Medium. https://medium.com/inst414-data-science-tech/clustering-soccer-players-based-on-match-activity-b8bfada84276

Michalczyk, K. (2019). Identifying patterns in build-up play using clustering. *Stats Perform OptaPro Forum*. https://www.statsperform.com/resource/identifying-patterns-in-build-up-play-using-clustering/

### Data Sources & Tools

StatsBomb. (2024). *Open Data Repository*. GitHub. https://github.com/statsbomb/open-data

StatsBomb. (2024). *Open Data Events v4.0.0 Specification*. https://github.com/statsbomb/open-data/blob/master/doc/Open%20Data%20Events%20v4.0.0.pdf

Carrasquilla, L. (2026). Complete guide on working with the StatsBomb Open Data dataset. *Medium*. https://medium.com/@lucascarrasquillaparra/complete-guide-on-working-with-the-statsbomb-open-data-dataset-a57c26d5852b

Rowlinson, A. (2023). *mplsoccer: A Python library for plotting soccer/football charts in Matplotlib*. Version 1.3.0. https://mplsoccer.readthedocs.io/

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., ... & Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825-2830.

### Soccer Analytics Platforms

FBref.com. (2024). *Football Statistics and History*. Sports Reference LLC. https://fbref.com/

Understat. (2024). *Expected Goals (xG) Statistics and Analysis*. https://understat.com/

Hudl StatsBomb. (2024). *Event Data & Analytics Platform*. https://statsbomb.com/what-we-do/soccer-data/

### Statistical Methods

Mann, H. B., & Whitney, D. R. (1947). On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics*, 18(1), 50-60.

Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65.

Efron, B., & Tibshirani, R. J. (1994). *An Introduction to the Bootstrap*. Chapman and Hall/CRC.

### Python Libraries & Software

McKinney, W. (2010). Data structures for statistical computing in Python. In *Proceedings of the 9th Python in Science Conference* (Vol. 445, pp. 51-56).

Harris, C. R., Millman, K. J., van der Walt, S. J., et al. (2020). Array programming with NumPy. *Nature*, 585(7825), 357-362.

Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90-95.

---

## APPENDICES

### A. Position Mapping Code
```python
POSITION_BIN_MAP = {
    "Center Back": "Center Back",
    "Left Center Back": "Center Back",
    ...
}
```

### B. Feature Formulas
- Progression-weighted: [formula]
- Zone-adjusted: [formula]
- Control score: [formula]
- Attacking index: [formula]

### C. Clustering Hyperparameters
- Algorithm: [name]
- k: [value]
- Distance: [metric]
- Init: [method]
- Seed: 42

### D. Statistical Test Outputs
- Full Mann-Whitney results by position
- Chi-square contingency table
- Bootstrap distributions

### E. Competition Coverage
| Competition | Matches | xG-Parity | % |
|-------------|---------|-----------|---|
| ... | ... | ... | ... |

### F. Code Repository
[GitHub link if public]

### G. Dashboard User Guide
[Full screenshots and instructions]

---

## DOCUMENT METADATA

**Version History:**
- v1.0: Initial outline (Feb 2026)
- v2.0: Sections 1-5 complete (Mar 2026)
- v3.0: Clustering complete (Apr 2026)
- v4.0: Final (Apr 2026)

**Word Count Target:** 8,000-10,000 words  
**Page Count Target:** 20-30 pages  
**Status:** [% complete]

**Next Steps:**
1. Run statistical tests (Section 5.4)
2. Feature engineering (Section 6.1)
3. Clustering (Section 6.3-6.5)
4. Dashboard (Section 8)
5. User testing (Section 7.5)
6. Write executive summary (Section 0)

---

**END OF OUTLINE**
