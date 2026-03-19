# Final Project Proposal

**GitHub Repo URL**: TODO

A short summary (3-4 paragraphs, about one page) of the data science problem you are addressing and what your solution will address. Feel free to include a figure or sketch to illustrate your project.

Each group should submit the URL pointing to this document on your github repo.


Clash Royale Meta Analysis: Card Counters and the Impact of Balance Changes

Clash Royale is a competitive mobile card game where players construct 8-card decks and battle in real-time across a global ranked ladder. Supercell, the developer, regularly releases balance patches to maintain competitive fairness. This project leverages the Clash Royale Season 18 Ladder Dataset published on Kaggle by bwandowando — a collection of 37.9 million distinct ladder matches recorded between December 3–20, 2020, gathered via the official Clash Royale API across 300,000+ clans. The dataset captures rich per-battle information including both players' full 8-card decks, starting trophy counts, average elixir costs, legendary card counts, and an explicit winner/loser label, making it well-suited for competitive meta analysis.

The first data science question, which card statistically counters another, treats each battle as a natural experiment. When a player's deck contains card A and their opponent's deck contains card B or other varying combinations, we can isolate and measure the conditional win rate of that matchup across all 37.9 million battles. With dataset of this scale, even rare card pairings accumulate thousands of observations. We apply proportion z-tests to determine which counter relationships are statistically significant versus sampling noise, producing a card-vs-card counter matrix that quantifies the strength and confidence of every matchup.

The second question: do balance changes measurably alter gameplay. This uses the temporal spread of the dataset (Dec 3–20, 2020) alongside known Supercell patch notes to frame balance patches as intervention events. By computing win rates and usage rates per card across the 18-day window and comparing pre- vs. post-patch periods, we test whether targeted nerfs or buffs produce statistically significant shifts in a card's win rate and popularity. 

Together, these analyses move the conversation about game balance from player intuition to statistical evidence. The output will be an interactive Streamlit dashboard that presents the card counter matrix, win rate distributions, and balance shift visualizations, giving both data scientists and the broader Clash Royale community a rigorous, reproducible lens on whether the game's meta is fair and whether developer interventions actually work.
