"""
Preprocessing script for Clash Royale Season 18 dataset.
Reads CSV battle data, computes aggregated statistics, saves as parquet for fast loading.
"""

import pandas as pd
import numpy as np
import os
import glob

DATA_DIR = "data/battle_data"
CARD_ATTRS_FILE = "data/clash_wiki_dataset.csv"
OUTPUT_DIR = "data/processed"

# Clash Royale card ID -> name mapping (Season 18, December 2020)
CARD_ID_TO_NAME = {
    26000000: "Knight", 26000001: "Archers", 26000002: "Goblins",
    26000003: "Giant", 26000004: "P.E.K.K.A.", 26000005: "Minions",
    26000006: "Balloon", 26000007: "Witch", 26000008: "Barbarians",
    26000009: "Golem", 26000010: "Skeletons", 26000011: "Valkyrie",
    26000012: "Skeleton Army", 26000013: "Bomber", 26000014: "Musketeer",
    26000015: "Baby Dragon", 26000016: "Prince", 26000017: "Wizard",
    26000018: "Mini P.E.K.K.A.", 26000019: "Spear Goblins",
    26000020: "Giant Skeleton", 26000021: "Hog Rider",
    26000022: "Minion Horde", 26000023: "Ice Wizard",
    26000024: "Royal Giant", 26000025: "Guards",
    26000026: "Princess", 26000027: "Dark Prince",
    26000028: "Three Musketeers", 26000029: "Lava Hound",
    26000030: "Ice Spirit", 26000031: "Fire Spirits",
    26000032: "Miner", 26000033: "Sparky",
    26000034: "Bowler", 26000035: "Lumberjack",
    26000036: "Battle Ram", 26000037: "Inferno Dragon",
    26000038: "Ice Golem", 26000039: "Mega Minion",
    26000040: "Dart Goblin", 26000041: "Goblin Gang",
    26000042: "Electro Wizard", 26000043: "Elite Barbarians",
    26000044: "Hunter", 26000045: "Executioner",
    26000046: "Bandit", 26000047: "Royal Recruits",
    26000048: "Night Witch", 26000049: "Bats",
    26000050: "Royal Ghost", 26000051: "Ram Rider",
    26000052: "Zappies", 26000053: "Rascals",
    26000054: "Cannon Cart", 26000055: "Mega Knight",
    26000056: "Skeleton Barrel", 26000057: "Flying Machine",
    26000058: "Wall Breakers", 26000059: "Royal Hogs",
    26000060: "Goblin Giant", 26000061: "Fisherman",
    26000062: "Magic Archer", 26000063: "Electro Dragon",
    26000064: "Firecracker", 26000065: "Mighty Miner",
    26000066: "Elixir Golem", 26000067: "Battle Healer",
    26000068: "Skeleton King", 26000069: "Archer Queen",
    26000070: "Golden Knight", 26000071: "Monk",
    # Spells (27xxxxx)
    27000000: "Arrows", 27000001: "Fireball",
    27000002: "Rocket", 27000003: "Goblin Barrel",
    27000004: "The Log", 27000005: "Poison",
    27000006: "Freeze", 27000007: "Mirror",
    27000008: "Lightning", 27000009: "Zap",
    27000010: "Graveyard", 27000011: "Clone",
    27000012: "Rage", 27000013: "Royal Delivery",
    27000014: "Tornado", 27000015: "Giant Snowball",
    27000016: "Earthquake", 27000017: "Barbarian Barrel",
    27000018: "Heal Spirit",
    # Buildings (28xxxxx)
    28000000: "Cannon", 28000001: "Tesla",
    28000002: "Inferno Tower", 28000003: "Mortar",
    28000004: "X-Bow", 28000005: "Tombstone",
    28000006: "Furnace", 28000007: "Goblin Hut",
    28000008: "Barbarian Hut", 28000009: "Bomb Tower",
    28000010: "Elixir Collector", 28000011: "Goblin Cage",
    28000012: "Goblin Drill",
}

# Card rarity mapping
CARD_RARITY = {
    "Knight": "Common", "Archers": "Common", "Goblins": "Common",
    "Minions": "Common", "Barbarians": "Common", "Skeletons": "Common",
    "Bomber": "Common", "Spear Goblins": "Common", "Fire Spirits": "Common",
    "Minion Horde": "Common", "Royal Recruits": "Common", "Bats": "Common",
    "Skeleton Barrel": "Common", "Royal Hogs": "Common",
    "Zap": "Common", "Arrows": "Common", "Giant Snowball": "Common",
    "Cannon": "Common", "Mortar": "Common",
    # Rare
    "Giant": "Rare", "Witch": "Rare", "Valkyrie": "Rare",
    "Musketeer": "Rare", "Hog Rider": "Rare", "Royal Giant": "Rare",
    "Skeleton Army": "Rare", "Baby Dragon": "Rare", "Mini P.E.K.K.A.": "Rare",
    "Tombstone": "Rare", "Elixir Collector": "Rare", "Furnace": "Rare",
    "Goblin Hut": "Rare", "Goblin Barrel": "Rare", "Tesla": "Rare",
    "Bomb Tower": "Rare", "Cannon Cart": "Rare", "Flying Machine": "Rare",
    "Battle Ram": "Rare", "Ice Golem": "Rare", "Mega Minion": "Rare",
    "Dart Goblin": "Rare", "Goblin Gang": "Rare", "Ice Spirit": "Rare",
    "Elite Barbarians": "Rare", "Wall Breakers": "Rare",
    "Fireball": "Rare", "Rage": "Rare", "Rocket": "Rare",
    # Epic
    "P.E.K.K.A.": "Epic", "Balloon": "Epic", "Golem": "Epic",
    "Giant Skeleton": "Epic", "Wizard": "Epic", "Prince": "Epic",
    "Skeleton Army": "Epic", "Dark Prince": "Epic",
    "Three Musketeers": "Epic", "Guards": "Epic", "Bowler": "Epic",
    "Lumberjack": "Epic", "Executioner": "Epic", "Night Witch": "Epic",
    "X-Bow": "Epic", "Barbarian Hut": "Epic", "Sparky": "Epic",
    "Mega Knight": "Epic", "Goblin Giant": "Epic", "Electro Dragon": "Epic",
    "Elixir Golem": "Epic", "Mighty Miner": "Epic",
    "Poison": "Epic", "Lightning": "Epic", "Freeze": "Epic",
    "Tornado": "Epic", "Graveyard": "Epic", "Clone": "Epic",
    "Mirror": "Epic", "Earthquake": "Epic",
    # Legendary
    "Ice Wizard": "Legendary", "Princess": "Legendary", "Inferno Dragon": "Legendary",
    "Miner": "Legendary", "Sparky": "Legendary", "Lava Hound": "Legendary",
    "Hunter": "Legendary", "Bandit": "Legendary", "Royal Ghost": "Legendary",
    "Ram Rider": "Legendary", "Zappies": "Legendary", "Rascals": "Legendary",
    "Magic Archer": "Legendary", "Fisherman": "Legendary",
    "Firecracker": "Legendary", "Battle Healer": "Legendary",
    "Skeleton King": "Legendary", "Archer Queen": "Legendary",
    "Golden Knight": "Legendary", "Monk": "Legendary",
    "The Log": "Legendary", "Barbarian Barrel": "Legendary",
    "Royal Delivery": "Legendary",
}

CARD_ELIXIR = {
    "Knight": 3, "Archers": 3, "Goblins": 2, "Giant": 5, "P.E.K.K.A.": 7,
    "Minions": 3, "Balloon": 5, "Witch": 5, "Barbarians": 5, "Golem": 8,
    "Skeletons": 1, "Valkyrie": 4, "Skeleton Army": 3, "Bomber": 2,
    "Musketeer": 4, "Baby Dragon": 4, "Prince": 5, "Wizard": 5,
    "Mini P.E.K.K.A.": 4, "Spear Goblins": 2, "Giant Skeleton": 6,
    "Hog Rider": 4, "Minion Horde": 5, "Ice Wizard": 3, "Royal Giant": 6,
    "Guards": 3, "Princess": 3, "Dark Prince": 4, "Three Musketeers": 9,
    "Lava Hound": 7, "Ice Spirit": 1, "Fire Spirits": 2, "Miner": 3,
    "Sparky": 6, "Bowler": 5, "Lumberjack": 4, "Battle Ram": 4,
    "Inferno Dragon": 4, "Ice Golem": 2, "Mega Minion": 3, "Dart Goblin": 3,
    "Goblin Gang": 3, "Electro Wizard": 4, "Elite Barbarians": 6,
    "Hunter": 4, "Executioner": 5, "Bandit": 3, "Royal Recruits": 7,
    "Night Witch": 4, "Bats": 2, "Royal Ghost": 3, "Ram Rider": 5,
    "Zappies": 4, "Rascals": 5, "Cannon Cart": 5, "Mega Knight": 7,
    "Skeleton Barrel": 3, "Flying Machine": 4, "Wall Breakers": 2,
    "Royal Hogs": 5, "Goblin Giant": 6, "Fisherman": 3, "Magic Archer": 4,
    "Electro Dragon": 5, "Firecracker": 3, "Mighty Miner": 4,
    "Elixir Golem": 3, "Battle Healer": 4,
    "Arrows": 3, "Fireball": 4, "Rocket": 6, "Goblin Barrel": 3,
    "The Log": 2, "Poison": 4, "Freeze": 4, "Mirror": 1,
    "Lightning": 6, "Zap": 2, "Graveyard": 5, "Clone": 3,
    "Rage": 2, "Royal Delivery": 3, "Tornado": 3, "Giant Snowball": 2,
    "Earthquake": 3, "Barbarian Barrel": 2, "Heal Spirit": 1,
    "Cannon": 3, "Tesla": 4, "Inferno Tower": 5, "Mortar": 4,
    "X-Bow": 6, "Tombstone": 3, "Furnace": 4, "Goblin Hut": 5,
    "Barbarian Hut": 7, "Bomb Tower": 5, "Elixir Collector": 6,
    "Goblin Cage": 4, "Goblin Drill": 4,
}


def load_battle_data(sample_frac=0.3):
    """Load battle data from all CSV files, optionally sampling."""
    csv_files = []
    for folder in sorted(os.listdir(DATA_DIR)):
        folder_path = os.path.join(DATA_DIR, folder)
        if os.path.isdir(folder_path):
            for f in os.listdir(folder_path):
                if f.endswith(".csv"):
                    csv_files.append(os.path.join(folder_path, f))

    print(f"Found {len(csv_files)} CSV files")
    dfs = []
    for f in csv_files:
        print(f"Loading {f}...")
        try:
            df = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
        except Exception as e:
            print(f"  Warning: could not read {f}: {e}, skipping.")
            continue
        if sample_frac < 1.0:
            df = df.sample(frac=sample_frac, random_state=42)
        dfs.append(df)

    battles = pd.concat(dfs, ignore_index=True)
    print(f"Total battles loaded: {len(battles):,}")
    return battles


def compute_card_stats(battles):
    """Compute per-card win rates and appearance rates."""
    card_cols_w = [f"winner.card{i}.id" for i in range(1, 9)]
    card_cols_l = [f"loser.card{i}.id" for i in range(1, 9)]

    card_wins = {}
    card_total = {}

    for col in card_cols_w:
        for cid in battles[col].dropna().astype(int):
            card_wins[cid] = card_wins.get(cid, 0) + 1
            card_total[cid] = card_total.get(cid, 0) + 1

    for col in card_cols_l:
        for cid in battles[col].dropna().astype(int):
            card_total[cid] = card_total.get(cid, 0) + 1

    total_battles = len(battles)
    records = []
    for cid, total in card_total.items():
        wins = card_wins.get(cid, 0)
        name = CARD_ID_TO_NAME.get(cid, f"Card_{cid}")
        rarity = CARD_RARITY.get(name, "Unknown")
        elixir = CARD_ELIXIR.get(name, 0)
        records.append({
            "card_id": cid,
            "card_name": name,
            "rarity": rarity,
            "elixir_cost": elixir,
            "total_appearances": total,
            "wins": wins,
            "win_rate": wins / total if total > 0 else 0.5,
            "appearance_rate": total / (total_battles * 2),  # 2 decks per battle
        })

    return pd.DataFrame(records).sort_values("total_appearances", ascending=False)


def compute_deck_cost_winrate(battles):
    """Bin deck elixir cost and compute win rates per bin."""
    records = []
    for _, row in battles.iterrows():
        records.append({
            "avg_elixir": row["winner.elixir.average"],
            "outcome": 1,
        })
        records.append({
            "avg_elixir": row["loser.elixir.average"],
            "outcome": 0,
        })

    df = pd.DataFrame(records).dropna()
    df = df[(df["avg_elixir"] >= 1.5) & (df["avg_elixir"] <= 6.0)]

    bins = np.arange(1.5, 6.25, 0.25)
    df["cost_bin"] = pd.cut(df["avg_elixir"], bins=bins)
    grouped = df.groupby("cost_bin", observed=True).agg(
        count=("outcome", "count"),
        win_rate=("outcome", "mean"),
    ).reset_index()
    grouped["cost_bin_mid"] = grouped["cost_bin"].apply(lambda x: x.mid)
    grouped["cost_bin"] = grouped["cost_bin"].astype(str)
    return grouped


def compute_level_advantage(battles):
    """Compute card level advantage (winner - loser) and win probability."""
    battles = battles.copy()
    battles["level_advantage"] = (
        battles["winner.totalcard.level"] - battles["loser.totalcard.level"]
    ) / 8  # avg per card

    df = battles[["level_advantage"]].copy()
    df["outcome"] = 1
    df_loser = pd.DataFrame({
        "level_advantage": -battles["level_advantage"],
        "outcome": 0,
    })
    combined = pd.concat([df, df_loser], ignore_index=True)
    combined = combined[combined["level_advantage"].between(-5, 5)]

    bins = np.arange(-5, 5.5, 0.5)
    combined["level_bin"] = pd.cut(combined["level_advantage"], bins=bins)
    grouped = combined.groupby("level_bin", observed=True).agg(
        count=("outcome", "count"),
        win_rate=("outcome", "mean"),
    ).reset_index()
    grouped["level_bin_mid"] = grouped["level_bin"].apply(lambda x: x.mid)
    grouped["level_bin"] = grouped["level_bin"].astype(str)
    return grouped


def compute_rarity_stats(card_stats):
    """Aggregate card stats by rarity."""
    return card_stats.groupby("rarity").agg(
        avg_win_rate=("win_rate", "mean"),
        median_win_rate=("win_rate", "median"),
        num_cards=("card_name", "count"),
        total_appearances=("total_appearances", "sum"),
    ).reset_index()


def compute_trophy_level_stats(battles):
    """Card level disparity grouped by trophy range."""
    battles = battles.copy()
    battles["avg_trophy"] = (
        battles["winner.startingTrophies"] + battles["loser.startingTrophies"]
    ) / 2
    battles["level_diff"] = (
        (battles["winner.totalcard.level"] - battles["loser.totalcard.level"]) / 8
    ).abs()

    bins = [0, 4000, 5000, 6000, 8000]
    labels = ["<4000", "4000-5000", "5000-6000", "6000+"]
    battles["trophy_range"] = pd.cut(battles["avg_trophy"], bins=bins, labels=labels)
    result = (
        battles.groupby("trophy_range", observed=True)["level_diff"]
        .agg(["mean", "median", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_level_diff", "median": "median_level_diff", "count": "battle_count"})
    )
    result["trophy_range"] = result["trophy_range"].astype(str)
    return result


def compute_counter_matrix(battles, top_n=60):
    """
    Compute card-vs-card win rates for the top N most-used cards.
    win_rate(A, B) = P(win | player has A in deck AND opponent has B in deck).
    """
    print("  Identifying top cards...")
    card_cols_w = [f"winner.card{i}.id" for i in range(1, 9)]
    card_cols_l = [f"loser.card{i}.id" for i in range(1, 9)]

    all_counts: dict = {}
    for col in card_cols_w + card_cols_l:
        for cid in battles[col].dropna().astype(int):
            all_counts[cid] = all_counts.get(cid, 0) + 1
    top_ids = set(sorted(all_counts, key=lambda x: -all_counts[x])[:top_n])

    print("  Building winner/loser card pair table...")
    battles_ri = battles.reset_index(drop=True)
    battles_ri.index.name = "bid"

    w_long = (
        battles_ri[card_cols_w]
        .reset_index()
        .melt(id_vars="bid", value_vars=card_cols_w, value_name="card_a")
        .dropna()
    )
    w_long["card_a"] = w_long["card_a"].astype(int)
    w_long = w_long[w_long["card_a"].isin(top_ids)][["bid", "card_a"]]

    l_long = (
        battles_ri[card_cols_l]
        .reset_index()
        .melt(id_vars="bid", value_vars=card_cols_l, value_name="card_b")
        .dropna()
    )
    l_long["card_b"] = l_long["card_b"].astype(int)
    l_long = l_long[l_long["card_b"].isin(top_ids)][["bid", "card_b"]]

    print("  Merging pairs (may take a moment)...")
    pairs = w_long.merge(l_long, on="bid")
    wins = pairs.groupby(["card_a", "card_b"]).size().reset_index(name="wins_a_vs_b")

    # total(A,B) = wins(A beats B) + wins(B beats A)
    wins_rev = wins.rename(
        columns={"card_a": "card_b", "card_b": "card_a", "wins_a_vs_b": "wins_b_vs_a"}
    )
    merged = wins.merge(wins_rev, on=["card_a", "card_b"], how="left").fillna(0)
    merged["total"] = merged["wins_a_vs_b"] + merged["wins_b_vs_a"]
    merged = merged[merged["total"] >= 200]
    merged["win_rate"] = merged["wins_a_vs_b"] / merged["total"]

    merged["card_a"] = merged["card_a"].map(lambda x: CARD_ID_TO_NAME.get(x, f"Card_{x}"))
    merged["card_b"] = merged["card_b"].map(lambda x: CARD_ID_TO_NAME.get(x, f"Card_{x}"))

    return merged[["card_a", "card_b", "wins_a_vs_b", "total", "win_rate"]]


def compute_deck_records(battles):
    """
    Store each deck (winner + loser) as a pipe-delimited string of sorted card names.
    Enables arbitrary card-combination win-rate queries at runtime.
    """
    card_cols_w = [f"winner.card{i}.id" for i in range(1, 9)]
    card_cols_l = [f"loser.card{i}.id" for i in range(1, 9)]
    name_map = CARD_ID_TO_NAME

    w_arr = battles[card_cols_w].fillna(0).astype(int).values
    l_arr = battles[card_cols_l].fillna(0).astype(int).values
    w_elixir = battles["winner.elixir.average"].values if "winner.elixir.average" in battles.columns else np.full(len(battles), np.nan)
    l_elixir = battles["loser.elixir.average"].values  if "loser.elixir.average"  in battles.columns else np.full(len(battles), np.nan)

    records = []
    n = len(battles)
    for i in range(n):
        w_cards = sorted(name_map[x] for x in w_arr[i] if x in name_map)
        records.append({"cards_str": "|" + "|".join(w_cards) + "|", "win": 1, "avg_elixir": float(w_elixir[i])})
        l_cards = sorted(name_map[x] for x in l_arr[i] if x in name_map)
        records.append({"cards_str": "|" + "|".join(l_cards) + "|", "win": 0, "avg_elixir": float(l_elixir[i])})

    return pd.DataFrame(records)


def compute_card_pair_stats(battles):
    """
    For every pair of cards that co-appear in the same deck, compute
    co_appearances and win_rate_together (the deck containing both won).
    """
    from collections import defaultdict

    card_cols_w = [f"winner.card{i}.id" for i in range(1, 9)]
    card_cols_l = [f"loser.card{i}.id" for i in range(1, 9)]
    name_map = CARD_ID_TO_NAME

    pair_wins  = defaultdict(int)
    pair_total = defaultdict(int)

    w_arr = battles[card_cols_w].fillna(0).astype(int).values
    l_arr = battles[card_cols_l].fillna(0).astype(int).values
    n = len(battles)
    print(f"  Building pair stats over {n:,} battles…")

    for i in range(n):
        w_cards = sorted(name_map[x] for x in w_arr[i] if x in name_map)
        for ai in range(len(w_cards)):
            for bi in range(ai + 1, len(w_cards)):
                k = (w_cards[ai], w_cards[bi])
                pair_wins[k]  += 1
                pair_total[k] += 1

        l_cards = sorted(name_map[x] for x in l_arr[i] if x in name_map)
        for ai in range(len(l_cards)):
            for bi in range(ai + 1, len(l_cards)):
                k = (l_cards[ai], l_cards[bi])
                pair_total[k] += 1

    records = []
    for (a, b), total in pair_total.items():
        if total >= 200:
            wins = pair_wins.get((a, b), 0)
            records.append({
                "card_a": a, "card_b": b,
                "co_appearances": total,
                "wins_together": wins,
                "win_rate_together": wins / total,
            })

    return pd.DataFrame(records).sort_values("co_appearances", ascending=False).reset_index(drop=True)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Loading battle data...")
    battles = load_battle_data(sample_frac=0.3)

    print("Computing card stats...")
    card_stats = compute_card_stats(battles)
    card_stats.to_parquet(f"{OUTPUT_DIR}/card_stats.parquet", index=False)
    print(f"  Saved card_stats: {len(card_stats)} cards")

    print("Computing deck cost vs win rate...")
    deck_cost = compute_deck_cost_winrate(battles)
    deck_cost.to_parquet(f"{OUTPUT_DIR}/deck_cost_winrate.parquet", index=False)

    print("Computing level advantage analysis...")
    level_adv = compute_level_advantage(battles)
    level_adv.to_parquet(f"{OUTPUT_DIR}/level_advantage.parquet", index=False)

    print("Computing rarity stats...")
    rarity_stats = compute_rarity_stats(card_stats)
    rarity_stats.to_parquet(f"{OUTPUT_DIR}/rarity_stats.parquet", index=False)

    print("Computing trophy range level stats...")
    trophy_level = compute_trophy_level_stats(battles)
    trophy_level.to_parquet(f"{OUTPUT_DIR}/trophy_level_stats.parquet", index=False)

    # Save summary stats
    summary = {
        "total_battles": len(battles),
        "unique_cards": card_stats["card_name"].nunique(),
        "date_range": "Dec 2020 – Jan 2021",
        "avg_trophies": battles["winner.startingTrophies"].mean(),
    }
    pd.DataFrame([summary]).to_parquet(f"{OUTPUT_DIR}/summary.parquet", index=False)

    print("Computing counter matrix (top 60 cards)...")
    counter_mx = compute_counter_matrix(battles)
    counter_mx.to_parquet(f"{OUTPUT_DIR}/counter_matrix.parquet", index=False)
    print(f"  Saved counter_matrix: {len(counter_mx)} card pairs")

    print("Computing deck records for combination queries…")
    deck_records = compute_deck_records(battles)
    deck_records.to_parquet(f"{OUTPUT_DIR}/deck_records.parquet", index=False)
    print(f"  Saved deck_records: {len(deck_records):,} rows")

    print("Computing card pair co-occurrence stats…")
    pair_stats = compute_card_pair_stats(battles)
    pair_stats.to_parquet(f"{OUTPUT_DIR}/card_pair_stats.parquet", index=False)
    print(f"  Saved card_pair_stats: {len(pair_stats):,} pairs")

    print("Done! All processed data saved to", OUTPUT_DIR)


if __name__ == "__main__":
    main()
