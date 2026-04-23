# Season 18 Clash Royale Deck Builder: A Data-Driven Approach to Deck Construction and Meta Analysis

---

## 1. Introduction

Clash Royale is a real-time strategy mobile game combining elements of collectible card games, tower defense, and multiplayer online battle arena games. It is one of the most popular mobile games in the world with over 1 million daily users [1]. In Clash Royale, two players are matched against each other with the objective of destroying each other's towers in 3 minutes of regular gameplay. Each player creates an 8-card deck before the match by selecting 8 cards from the 100+ cards available.

Each card is quite distinct. Cards differ in rarity, troop type, elixir cost, hitpoints, damage output, damage type, and special abilities. This variety combinatorically creates over a billion possible deck configurations, producing an enormous space of offensive and defensive interactions. Some cards work very well together within the same deck; some deck constructs counter other decks so effectively that the conclusion to the match is almost predictable. While player skill contributes significantly to match outcomes, the synergies between cards within a deck cannot be discounted.

We use the Season 18 Ladder Dataset published on Kaggle, which consists of 37.9 million distinct match records, to discover what synergies and counters exist in Clash Royale. Additionally, we analyze which cards are popular and whether there is a correlation between popularity and effectiveness. Lastly, we analyze whether average deck elixir cost affects win rate. We combine these three analytical approaches to create the **Season 18 Clash Royale Deck Builder**, an interactive tool that allows a player to build a deck and receive comprehensive analytics including deck archetype, swap suggestions, and possible threats. Ultimately, the analysis and Deck Builder give players crucial insight without requiring them to test new deck configurations in an actual match where a loss risks rank on the leaderboard.

---

## 2. Related Work

Several websites offer Clash Royale deck builders, and most provide recommendations based on the decks currently used by top-ranked players. While the idea is sound, top players do tend to identify strong synergies, this approach assumes that regular players can extract the same benefit from complex, technically demanding strategies that professionals employ. There is no guarantee that a deck optimized for high-level mechanical play translates well to a broader player base.

Other deck-building sites claim to use AI to generate recommendations, but these tools do not disclose their backend algorithms, making it impossible for users to understand or evaluate the basis for any given suggestion. Our approach differs in two key ways: it is grounded directly in empirical win-rate data drawn from millions of matches across the full player population, and every recommendation is traceable to a transparent statistical methodology.

---

## 3. Methods

Our methodology consists of a preprocessing pipeline that computes several statistical structures from the raw battle data, and a Streamlit-based front-end that queries those structures interactively.

**Data Loading and Sampling.** Due to the scale of the dataset (37.9 million records), we load all CSV files and apply a 30% random sample, yielding approximately 11 million battles. This reduces computation time while preserving statistical representativeness across the full season.

**Per-Card Win Rate and Appearance Rate.** For each card, we compute a win rate as the number of appearances in winning decks divided by total appearances across all decks. Appearance rate is normalized by total battles multiplied by two, since each battle contains two decks. These metrics form the backbone of the Card Stats and Overview pages, and inform the individual win rate component of the Deck Builder's synergy scoring.

**Deck Cost vs. Win Rate.** We bin each deck's average elixir cost into 0.25-wide intervals ranging from 1.5 to 6.0 and compute the win rate per bin. This analysis powers the Deck Cost Analysis page and the meta win rate curve displayed in the Deck Builder, which shows where a user's constructed deck falls relative to the season-wide trend.

**Card Level Advantage Analysis.** We compute the difference in average card level between the winner and loser of each battle, normalized per card, and bin it to plot win probability as a function of level advantage. This analysis investigates pay-to-win dynamics and is presented on the Card Level Impact page.

**Counter Matrix.** For the top 60 most-used cards we compute P(win | player has card A, opponent has card B) across all battles. This is done by joining winner and loser card tables on battle ID to enumerate every cross-deck card pair, then computing win rates filtered to pairs with at least 200 encounters for statistical reliability. The resulting pairwise win rate matrix directly powers the Biggest Threats feature in the Deck Builder, which identifies cards outside the user's deck that historically perform well against cards within it.

**Card Pair Co-occurrence and Synergy.** For every pair of cards co-appearing in the same deck, we compute co-appearance frequency and the win rate of decks containing both cards. Pairs with fewer than 200 appearances are excluded. This produces a synergy table used directly in the Deck Builder's swap suggestion engine.

**Deck Records for Combination Queries.** Each deck is serialized as a pipe-delimited, sorted string of card names and stored in a flat table. At query time, substring matching over this table retrieves all decks containing a given set of cards, enabling arbitrary multi-card combination win rate lookups in the Card Combination Analysis feature.

**Deck Builder Synergy Scoring.** Swap suggestions are generated by scoring each candidate card using a weighted formula: 60% of the score comes from the average pairwise win rate between the candidate and the other seven deck cards, and 40% from the candidate's individual win rate. The three deck cards with the lowest synergy scores are identified as the weakest links. Replacement candidates are then ranked by net score improvement, with a small penalty applied for large changes in elixir cost to preserve deck balance.

**Archetype Classification.** We apply a rule-based classifier to label each constructed deck with one of five archetypes: Cycle, Control, Midrange, Beatdown, or Siege. Classification is based on average elixir cost and the count of each card type (troops, spells, buildings) in the deck. For example, a deck with two or more buildings and an average elixir cost of 3.8 or above is classified as Siege. This label is displayed in the Deck Builder to give users immediate strategic context for their deck.

---

## 4. Results

**Overview Page.** The Overview page gives new players a high-level snapshot of the Season 18 meta. The top 15 most popular cards are displayed as a natural starting point, alongside a popularity vs. win rate scatter plot that surfaces which cards are both widely used and effective.

**Card Stats Page.** The Card Stats page offers a deeper look at each card's individual win rate and appearance rate. Users can filter by rarity, set a minimum appearance threshold, and compare cards side by side. The most notable feature on this page is the **Card Combination Analysis**, which allows users to select 2 to 8 cards and immediately see the average win rate of all Season 18 decks containing that exact combination. This feature provides a direct, empirical test of any synergy hypothesis.

**Rarity & Pay-to-Win Page.** This page examines whether rarer cards carry higher win rates, effectively asking whether players who spend money to unlock and level up Legendary or Epic cards gain a measurable competitive advantage. Our analysis shows that win rates across Common, Rare, Epic, and Legendary cards do not diverge in any meaningful way, suggesting that rarity alone is not a reliable predictor of card effectiveness.

**Card Level Impact Page.** This page quantifies the effect of card level on match outcomes. While a level advantage does increase win probability at lower trophy ranges, the data shows that players near the top of the leaderboard have opponents at nearly identical card levels, effectively removing level as a confounding variable in high-level deck analysis.

**Deck Cost Analysis Page.** This page demonstrates that a minimum average elixir cost of approximately 2.6 is required to construct a viable deck. Win rate is not significantly affected for decks above this threshold, but drops steeply for cheaper decks, suggesting that extremely low-cost cycle strategies lack the tools to handle the variety of threats present in the Season 18 meta.

**Deck Builder Page.** The Deck Builder is the central deliverable of this project. A player selects up to 8 cards from a searchable, filterable card pool and receives a full suite of analytics: average elixir cost, deck archetype, per-card win rates, a rarity breakdown, swap suggestions ranked by synergy score, and the top five cards outside the deck that pose the greatest historical threat to its card composition. Figure 1 below illustrates a sample Cycle deck and its full analysis output.

---

## 5. Discussion

This analysis of Clash Royale Season 18 uses a distinctive metric to evaluate deck quality: empirical win rate derived from millions of real matches, rather than imitation of top-player patterns. The reasoning is straightforward: the objective of every match is to win, so a deck builder that directly optimizes for win rate should produce more broadly applicable recommendations than one that mirrors the habits of a small elite.

In practice, this means the Deck Builder can surface non-obvious card combinations that perform well across the full player population but may never appear in a professional player's deck. It also means that recommendations are transparent and falsifiable: every swap suggestion and threat alert traces back to a concrete statistical computation that users can interrogate on the Card Stats and Card Combination pages.

A recurring complaint in the Clash Royale community is that decks converge toward a small number of dominant configurations as a season progresses, making the latter half of each season feel repetitive. A deck builder grounded in win rate rather than player trends has the potential to resist this convergence, surfacing viable alternatives that the community may not have collectively discovered yet. We hope this tool contributes positively to deck diversity and keeps competition fresh throughout the season.

---

## 6. Future Work

This project was built using Season 18 data from December 2020. The most immediate improvement would be updating the pipeline to ingest data from the current season, ensuring that recommendations remain relevant to today's card pool and meta.

Beyond data freshness, the swap recommendation engine could be enriched with domain knowledge. The current scoring formula considers only pairwise win rate and elixir cost, but does not account for a deck's win condition (the primary card or combination a player builds around to destroy towers) or the distribution of card types. Penalizing swaps that disrupt the win condition or create a type imbalance (for example, leaving a deck with no spell to handle swarms) could meaningfully improve recommendation quality.

Finally, expanding the counter matrix beyond the top 60 cards and incorporating trophy-range segmentation would allow the Deck Builder to tailor suggestions to a player's specific skill bracket, since the optimal deck at 4,000 trophies may differ substantially from the optimal deck at 7,000.

---

## References

[1] ActivePlayer.io. *Clash Royale Live Player Count and Statistics.* https://activeplayer.io/clash-royale/

[2] Kaggle. *Clash Royale Season 18 Ladder Dataset.* https://www.kaggle.com/

---
