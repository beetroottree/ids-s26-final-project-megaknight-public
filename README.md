[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/7URWNQLZ)

# Season 18 Clash Royale Deck Builder

**Carnegie Mellon University — Interactive Data Science (Spring 2026)**

![Deck Builder Overview](screenshots/final_report/deck_builder.png)

---

## Team Members

| Name | Email |
|---|---|
| Nihar Atri *(contact)* | npatri@andrew.cmu.edu |
| Hou Kin Wan | houkinw@andrew.cmu.edu |
| Natan Zmudzinski | nzmudzin@andrew.cmu.edu |
| Andrew Zhang | andrewz2@andrew.cmu.edu |

---

## Abstract

Clash Royale is a competitive mobile card game where players construct 8-card decks and battle in real time. With over 100 unique cards, the combinatorial deck space makes it nearly impossible to evaluate card choices without data (Over 1 billion different combinations!). This project analyzes 37.9 million ladder matches from Season 18 (December 2020) to answer three core questions: which cards and card combinations actually win, does card rarity or level confer a measurable competitive advantage, and how does average deck elixir cost relate to win rate? We present an interactive Streamlit dashboard — the **Season 18 Clash Royale Deck Builder** — that surfaces these findings through six analysis views and a fully interactive deck builder that provides synergy-aware swap suggestions, archetype classification, and counter-card alerts, all grounded in empirical match data rather than imitation of top-player trends.

---

## Paper

[Read the full project report](final_report.md)

---

## Video

*Link to be added — upload to Google Drive and paste here.*

---

## Application

*Deployed link to be added.*

To run locally, see the instructions below.

---

## Running Instructions

### 1. Clone the repository

```bash
git clone https://github.com/CMU-IDS-Assignments/ids-s26-final-project-megaknight.git
cd ids-s26-final-project-megaknight
```

### 2. Install dependencies


```bash
pip install -r requirements.txt
```

### 3. Launch the app

```bash
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501` by default.

---

## Project Screenshots

| | |
|---|---|
| ![Popular cards](screenshots/final_report/popular.png) | ![Card combo analysis](screenshots/final_report/card_combo_analysis.png) |
| *Top cards by appearance rate* | *Card Combination Analysis — empirical win rate for any card set* |
| ![Deck analysis](screenshots/final_report/deck_analysis.png) | ![Swap suggestions](screenshots/final_report/swaps.png) |
| *Full deck analysis: archetype, elixir curve, win rates* | *Synergy-aware swap suggestions with elixir delta warnings* |
| ![Threats](screenshots/final_report/threats.png) | |
| *Biggest Threats panel — cards that historically counter your deck* | |

---

## Work Distribution

| Member | Contributions |
|---|---|
| **Andrew Zhang** | App layout and structure, sidebar navigation, CSS styling, Card Stats tab (card detail lookup, combination analysis), preprocessing pipeline extensions (deck records, pair stats), swap suggestion engine rewrite |
| **Nihar Atri** | Bug fixes, visual polish, overall UX refinement, final report writing |
| **Hou Kin Wan** | Visualization design, data insights, analysis of rarity and pay-to-win findings |
| **Natan Zmudzinski** | Visualization design, data insights, deck cost and card level impact analysis |

---

## Process Commentary

The project started from a straightforward question — can we build a better Clash Royale deck builder using real match data instead of copying what top players use? The Season 18 dataset gave us the scale to do this rigorously: 37.9 million battles is large enough that even uncommon card pairings have thousands of observations.

The biggest technical challenge was compute. The full dataset is too large to query interactively, so we built an offline preprocessing pipeline that computes every statistic we need and stores it in compressed Parquet files. This meant the app could remain fully interactive without hitting any data loading delays at runtime.

The most surprising analytical finding was how flat win rates are across rarity tiers. Going in, we expected Legendary cards to show some measurable edge — they are harder and more expensive to obtain. The data shows they don't, which reframes the whole pay-to-win conversation around card levels rather than rarity.

The Deck Builder's swap suggestion engine went through two iterations. The first version simply ranked alternatives by individual win rate. The second — and current — version scores candidates by their pairwise win rate with the other seven deck cards, which produces meaningfully different (and better) recommendations. The card pair co-occurrence dataset, computed from all 11 million sampled battles, is what makes this possible.
