import hashlib
import html
import os
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

alt.data_transformers.disable_max_rows()



def _clash_dark_altair_theme():
    return {
        "config": {
            "background": "#0f1524",
            "view": {"stroke": "#283246"},
            "title": {"color": "#f2f4f8"},
            "axis": {
                "labelColor": "#d8deea",
                "titleColor": "#eef2f8",
                "domainColor": "#5f6e85",
                "gridColor": "#2e3a50",
                "tickColor": "#5f6e85",
            },
            "legend": {
                "labelColor": "#d8deea",
                "titleColor": "#eef2f8",
                "symbolStrokeColor": "#d8deea",
            },
            "header": {
                "labelColor": "#d8deea",
                "titleColor": "#eef2f8",
            },
            "mark": {"color": "#79c0ff"},
        }
    }

alt.themes.register("clash_dark", _clash_dark_altair_theme)
alt.themes.enable("clash_dark")


st.set_page_config(page_title="Clash Royale Meta Analyzer", page_icon="⚔️", layout="wide", initial_sidebar_state="expanded")

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_css_path = os.path.join(_APP_DIR, "streamlit_app.css")
if os.path.isfile(_css_path):
    with open(_css_path, encoding="utf-8") as _f:
        st.markdown(f"<style>{_f.read()}</style>", unsafe_allow_html=True)

PROCESSED_DIR = "data/processed"

RARITY_COLORS = {
    "Common": "#9E9E9E",
    "Rare": "#4FC3F7",
    "Epic": "#CE93D8",
    "Legendary": "#FFD54F",
    "Unknown": "#78909C",
}
RARITY_DOMAIN = list(RARITY_COLORS.keys())
RARITY_RANGE  = list(RARITY_COLORS.values())
RARITY_SCALE  = alt.Scale(domain=RARITY_DOMAIN, range=RARITY_RANGE)

def rarity_color_scale():
    return alt.Color("rarity:N", scale=RARITY_SCALE, legend=alt.Legend(title="Rarity"))

def card_image_url(card_name: str) -> str:
    slug = (
        card_name.lower()
        .replace("p.e.k.k.a.", "pekka")
        .replace("mini p.e.k.k.a.", "mini-pekka")
        .replace(".", "")
        .replace(" ", "-")
        .replace("--", "-")
    )
    return f"https://cdn.royaleapi.com/static/img/cards-150/{slug}.png"

def hline(y_val, color="gray", dash=[5, 3]):
    return (
        alt.Chart(pd.DataFrame({"y": [y_val]}))
        .mark_rule(strokeDash=dash, color=color, opacity=0.5)
        .encode(y=alt.Y("y:Q", axis=None))
    )

def vline(x_val, color="gray", dash=[5, 3]):
    return (
        alt.Chart(pd.DataFrame({"x": [x_val]}))
        .mark_rule(strokeDash=dash, color=color, opacity=0.5)
        .encode(x=alt.X("x:Q", axis=None))
    )

PAGES = [
    ("🏠", "Overview"),
    ("🃏", "Card Stats"),
    ("💎", "Rarity & Pay-to-Win"),
    ("📈", "Card Level Impact"),
    ("💰", "Deck Cost Analysis"),
    ("🛠️", "Deck Builder"),
]

if "page" not in st.session_state:
    st.session_state.page = "Overview"

with st.sidebar:
    st.markdown("<h2 class='sidebar-brand-title'>⚔️ Clash Royale</h2><p class='sidebar-brand-sub'>Meta Analyzer</p>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p class='sidebar-nav-label'>NAVIGATION</p>", unsafe_allow_html=True)

    for icon, name in PAGES:
        is_active = st.session_state.page == name
        if st.button(
            f"{icon}  {name}",
            key=f"nav_{name}",
            type="primary" if is_active else "secondary",
            use_container_width=True,
        ):
            st.session_state.page = name
            st.rerun()

    st.markdown("---")
    st.markdown("<p class='sidebar-meta'>Season 18 (Dec 2020) · ~6.8M battles · 102 cards</p>", unsafe_allow_html=True)

page = st.session_state.page

@st.cache_data
def load_all():
    files = {
        "card_stats": "card_stats.parquet",
        "deck_cost": "deck_cost_winrate.parquet",
        "level_adv": "level_advantage.parquet",
        "rarity_stats": "rarity_stats.parquet",
        "trophy_level": "trophy_level_stats.parquet",
        "summary": "summary.parquet",
    }
    return {
        k: pd.read_parquet(os.path.join(PROCESSED_DIR, v))
        for k, v in files.items()
        if os.path.exists(os.path.join(PROCESSED_DIR, v))
    }

@st.cache_data
def load_deck_records():
    path = os.path.join(PROCESSED_DIR, "deck_records.parquet")
    return pd.read_parquet(path) if os.path.exists(path) else None

@st.cache_data
def load_card_pair_stats():
    path = os.path.join(PROCESSED_DIR, "card_pair_stats.parquet")
    return pd.read_parquet(path) if os.path.exists(path) else None

data        = load_all()
card_stats  = data["card_stats"]
deck_cost   = data["deck_cost"]
level_adv   = data["level_adv"]
rarity_stats = data["rarity_stats"]
trophy_level = data["trophy_level"]
summary     = data["summary"].iloc[0]

def _card_type(cid):
    s = str(int(cid))
    if s.startswith("27"): return "Spell"
    if s.startswith("28"): return "Building"
    return "Troop"
card_stats["card_type"] = card_stats["card_id"].apply(_card_type)

if page == "Overview":
    st.title("⚔️ Clash Royale Meta Analyzer")
    st.caption("Season 18 ladder (~6.8M battles, Dec 2020).")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Battles",  f"{int(summary['total_battles']):,}")
    c2.metric("Unique Cards",   f"{int(summary['unique_cards'])}")
    c3.metric("Avg Trophies",   f"{summary['avg_trophies']:.0f}")
    c4.metric("Date Range",     "Dec 2020 – Jan 2021")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Top 15 Most Popular Cards")
        top_pop = card_stats.nlargest(15, "total_appearances").copy()
        chart = alt.Chart(top_pop).mark_bar().encode(
            x=alt.X("appearance_rate:Q", title="Appearance Rate", axis=alt.Axis(format=".0%")), y=alt.Y("card_name:N", sort="-x", title=""), color=rarity_color_scale(),
            tooltip=[alt.Tooltip("card_name:N", title="Card"), alt.Tooltip("rarity:N", title="Rarity"), alt.Tooltip("appearance_rate:Q", title="Appearance Rate", format=".1%"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%")],
        ).properties(height=460)
        st.altair_chart(chart, use_container_width=True)

    with col_r:
        st.subheader("Top 15 Highest Win Rate Cards")
        min_app = card_stats["total_appearances"].quantile(0.25)
        top_wr = card_stats[card_stats["total_appearances"] >= min_app].nlargest(15, "win_rate").copy()

        base_wr = alt.Chart(top_wr).encode(
            x=alt.X("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")),
            y=alt.Y("card_name:N", sort="-x", title="", axis=alt.Axis(labelFontSize=13, labelLimit=160)),
        )
        bars2 = base_wr.mark_bar().encode(
            color=rarity_color_scale(),
            tooltip=[
                alt.Tooltip("card_name:N", title="Card"),
                alt.Tooltip("rarity:N", title="Rarity"),
                alt.Tooltip("win_rate:Q", title="Win Rate", format=".2%"),
                alt.Tooltip("total_appearances:Q", title="Appearances"),
            ],
        )
        labels2 = base_wr.mark_text(align="left", dx=4, fontSize=12, fontWeight="bold").encode(
            text=alt.Text("win_rate:Q", format=".1%"),
            color=alt.value("white"),
        )
        rule50 = vline(0.5)
        st.altair_chart((bars2 + labels2 + rule50).properties(height=460), use_container_width=True)

    st.subheader("Popularity vs Win Rate — The Meta Quadrant")
    st.caption("Axes: appearance rate vs win rate. Bubble size = appearances.")
    median_app = float(card_stats["appearance_rate"].median())
    _ar_max = float(card_stats["appearance_rate"].max())
    _wr_max = float(card_stats["win_rate"].max())
    _pad = 0.04

    x_scale = alt.Scale(domain=[0, min(1.0, _ar_max * (1 + _pad) + 1e-9)], nice=False, zero=True)
    y_hi = min(1.0, max(0.5, _wr_max * (1 + _pad) + 1e-9))
    y_scale = alt.Scale(domain=[0, y_hi], nice=False, zero=True)

    scatter = alt.Chart(card_stats).mark_circle(opacity=0.8).encode(
        x=alt.X("appearance_rate:Q", title="Appearance Rate", axis=alt.Axis(format=".0%"), scale=x_scale),
        y=alt.Y("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%"), scale=y_scale),
        color=rarity_color_scale(),
        size=alt.Size("total_appearances:Q", scale=alt.Scale(range=[30, 700]), legend=None),
        tooltip=[
            alt.Tooltip("card_name:N", title="Card"),
            alt.Tooltip("rarity:N", title="Rarity"),
            alt.Tooltip("appearance_rate:Q", title="Appearance Rate", format=".1%"),
            alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%"),
            alt.Tooltip("total_appearances:Q", title="Appearances"),
        ],
    )
    h_mid = alt.Chart().mark_rule(strokeDash=[5, 3], color="gray", opacity=0.5).encode(y=alt.datum(0.5))
    v_mid = alt.Chart().mark_rule(strokeDash=[5, 3], color="gray", opacity=0.5).encode(x=alt.datum(median_app))

    meta_quad = alt.layer(scatter, h_mid, v_mid).properties(height=480)
    st.altair_chart(meta_quad, use_container_width=True)

elif page == "Card Stats":
    st.title("🃏 Card Popularity & Win Rates")

    _max_app = int(card_stats["total_appearances"].max())
    _slider_max_k = max(10, int(np.ceil(_max_app / 1000 / 10) * 10))

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        rarity_filter = st.multiselect("Filter by Rarity", options=["Common", "Rare", "Epic", "Legendary", "Unknown"], default=["Common", "Rare", "Epic", "Legendary"])
    with col_f2:
        min_sample = st.slider(
            "Minimum appearances (thousands)",
            0,
            _slider_max_k,
            10,
            10,
            help=(
                f"Keep cards with at least this many appearances in the sample. "
                f"Dataset peak ≈ {_max_app:,} (~{_slider_max_k}k); at 500k, many meta cards still qualify."
            ),
        )

    _min_abs = int(min_sample) * 1000
    filtered = card_stats[
        card_stats["rarity"].isin(rarity_filter) &
        (card_stats["total_appearances"] >= _min_abs)
    ].copy()
    st.caption(
        f"Showing **{len(filtered)}** of **{len(card_stats)}** cards "
        f"(appearances ≥ **{_min_abs:,}**, selected rarities)."
    )

    st.subheader("Top Cards at a Glance")
    st.caption(
        f"Same filters as above: **≥ {_min_abs:,}** appearances and selected rarities. "
        "Each tile shows **usage** (share of battles where the card appears) and **win rate**."
    )
    top_glance = filtered.nlargest(12, "total_appearances")
    if len(top_glance) == 0:
        st.caption("No cards match the current filters.")
    else:
        cells = []
        for _, row in top_glance.iterrows():
            cname = row["card_name"]
            esc_body = html.escape(cname)
            esc_alt = html.escape(cname, quote=True)
            url = card_image_url(cname)
            cells.append(
                f"<div class='glance-card-cell'>"
                f'<img src="{url}" alt="{esc_alt}" loading="lazy" />'
                f"<div class='glance-card-name'>{esc_body}</div>"
                f"<div class='glance-card-usage-label'>Usage in sample</div>"
                f"<div class='glance-card-usage'>{row['appearance_rate']:.1%}</div>"
                f"<div class='glance-card-wr'>Win rate: {row['win_rate']:.1%}</div>"
                f"</div>"
            )
        st.markdown(f"<div class='glance-grid'>{''.join(cells)}</div>", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 20 by Appearance Rate")
        top20_app = filtered.nlargest(20, "appearance_rate")
        chart = alt.Chart(top20_app).mark_bar().encode(
            x=alt.X("appearance_rate:Q", title="Appearance Rate", axis=alt.Axis(format=".0%")), y=alt.Y("card_name:N", sort="-x", title=""), color=rarity_color_scale(),
            tooltip=[alt.Tooltip("card_name:N", title="Card"), alt.Tooltip("rarity:N", title="Rarity"), alt.Tooltip("appearance_rate:Q", title="Appearance Rate", format=".1%"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%")],
        ).properties(height=560)
        st.altair_chart(chart, use_container_width=True)

    with col2:
        st.subheader("Win Rate — Top 20 Cards by Usage")
        top20_wr = filtered.nlargest(20, "total_appearances").sort_values("win_rate")
        chart2 = alt.Chart(top20_wr).mark_bar().encode(
            x=alt.X("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")), y=alt.Y("card_name:N", sort="x", title=""), color=rarity_color_scale(),
            tooltip=[alt.Tooltip("card_name:N", title="Card"), alt.Tooltip("rarity:N", title="Rarity"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%")],
        ).properties(height=560)
        st.altair_chart(chart2 + hline(0.5), use_container_width=True)

    st.subheader("Full Card Stats Table")
    display_df = filtered[["card_name","rarity","elixir_cost","total_appearances","wins","win_rate","appearance_rate"]].copy()
    display_df["win_rate"]        = (display_df["win_rate"]        * 100).round(2)
    display_df["appearance_rate"] = (display_df["appearance_rate"] * 100).round(2)
    display_df.columns = ["Card","Rarity","Elixir","Appearances","Wins","Win Rate %","Appearance Rate %"]
    st.dataframe(display_df.sort_values("Appearances", ascending=False), use_container_width=True, height=400)

    st.markdown("---")

    st.subheader("Card Detail Lookup")
    st.caption("Pick one or more cards to compare their stats side by side.")

    all_card_names = sorted(card_stats[~card_stats["card_name"].str.startswith("Card_")]["card_name"].tolist())
    detail_picks = st.multiselect(
        "Select cards", all_card_names, key="detail_picks",
        placeholder="Type a card name…",
    )

    if detail_picks:
        detail_df = card_stats[card_stats["card_name"].isin(detail_picks)].copy()

        img_cols = st.columns(min(len(detail_picks), 8))
        for i, (_, row) in enumerate(detail_df.iterrows()):
            with img_cols[i % 8]:
                st.image(card_image_url(row["card_name"]), width=80)
                rc = RARITY_COLORS.get(row["rarity"], "#aaa")
                st.markdown(
                    f"<div style='text-align:center;font-size:0.72rem'>"
                    f"<b>{row['card_name']}</b><br>"
                    f"<span style='color:{rc}'>■</span> {row['rarity']}<br>"
                    f"⚡{int(row['elixir_cost'])} &nbsp;·&nbsp; WR <b>{row['win_rate']:.1%}</b></div>",
                    unsafe_allow_html=True,
                )

        if len(detail_picks) > 1:
            ch_col1, ch_col2 = st.columns(2)
            with ch_col1:
                wr_chart = alt.Chart(detail_df).mark_bar().encode(
                    x=alt.X("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")),
                    y=alt.Y("card_name:N", sort="-x", title=""),
                    color=rarity_color_scale(),
                    tooltip=[alt.Tooltip("card_name:N"), alt.Tooltip("win_rate:Q", format=".2%"), alt.Tooltip("rarity:N")],
                ).properties(height=max(120, len(detail_picks) * 40))
                st.altair_chart(wr_chart + hline(0.5), use_container_width=True)
            with ch_col2:
                app_chart = alt.Chart(detail_df).mark_bar().encode(
                    x=alt.X("appearance_rate:Q", title="Appearance Rate", axis=alt.Axis(format=".1%")),
                    y=alt.Y("card_name:N", sort="-x", title=""),
                    color=rarity_color_scale(),
                    tooltip=[alt.Tooltip("card_name:N"), alt.Tooltip("appearance_rate:Q", format=".2%")],
                ).properties(height=max(120, len(detail_picks) * 40))
                st.altair_chart(app_chart, use_container_width=True)

        tbl = detail_df[["card_name","rarity","elixir_cost","card_type","total_appearances","wins","win_rate","appearance_rate"]].copy()
        tbl["win_rate"]        = (tbl["win_rate"]        * 100).round(2)
        tbl["appearance_rate"] = (tbl["appearance_rate"] * 100).round(2)
        tbl.columns = ["Card","Rarity","Elixir","Type","Appearances","Wins","Win Rate %","Appearance Rate %"]
        st.dataframe(tbl.sort_values("Win Rate %", ascending=False), use_container_width=True, hide_index=True)

    st.markdown("---")

    st.subheader("Card Combination Analysis")
    st.caption("Select 2–8 cards to see the win rate of decks containing ALL of them.")

    combo_picks = st.multiselect(
        "Select cards for combo", all_card_names, key="combo_picks",
        max_selections=8, placeholder="Pick 2 or more cards…",
    )

    if len(combo_picks) >= 2:
        deck_records_df = load_deck_records()
        pair_stats_df   = load_card_pair_stats()

        if deck_records_df is None:
            st.warning("deck_records.parquet not found — run preprocess.py first.")
        else:
            with st.spinner("Querying deck records…"):
                mask = pd.Series([True] * len(deck_records_df), index=deck_records_df.index)
                for card in combo_picks:
                    mask &= deck_records_df["cards_str"].str.contains(f"|{card}|", regex=False)
                combo_df = deck_records_df[mask]

            n_decks = len(combo_df)
            if n_decks == 0:
                st.warning("No decks found containing all selected cards. Try a different combination.")
            else:
                combo_wr = combo_df["win"].mean()
                combo_elixir = combo_df["avg_elixir"].mean()

                indiv_wrs = {
                    row["card_name"]: row["win_rate"]
                    for _, row in card_stats[card_stats["card_name"].isin(combo_picks)].iterrows()
                }
                avg_indiv_wr = np.mean(list(indiv_wrs.values())) if indiv_wrs else 0.5

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Combo Win Rate",    f"{combo_wr:.2%}")
                m2.metric("Avg Indiv Win Rate", f"{avg_indiv_wr:.2%}",
                          delta=f"{(combo_wr - avg_indiv_wr)*100:+.1f}pp")
                m3.metric("Decks Sampled",     f"{n_decks:,}")
                m4.metric("Avg Elixir",        f"{combo_elixir:.2f}")

                compare_data = [{"label": " + ".join(combo_picks), "win_rate": combo_wr, "kind": "Combo"}]
                for cname, wr in indiv_wrs.items():
                    compare_data.append({"label": cname, "win_rate": wr, "kind": "Individual"})
                compare_df = pd.DataFrame(compare_data)

                cmp_chart = alt.Chart(compare_df).mark_bar().encode(
                    x=alt.X("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")),
                    y=alt.Y("label:N", sort="-x", title=""),
                    color=alt.Color("kind:N", scale=alt.Scale(
                        domain=["Combo", "Individual"],
                        range=["#FFD54F", "#4FC3F7"],
                    ), legend=alt.Legend(title="")),
                    tooltip=[alt.Tooltip("label:N"), alt.Tooltip("win_rate:Q", format=".2%"), alt.Tooltip("kind:N")],
                ).properties(height=max(120, (len(combo_picks) + 1) * 40))
                st.altair_chart(cmp_chart + hline(0.5), use_container_width=True)

                if pair_stats_df is not None and len(combo_picks) >= 2:
                    st.markdown("**Pairwise co-occurrence stats within this combo:**")
                    from itertools import combinations as _comb
                    pair_rows = []
                    for a, b in _comb(sorted(combo_picks), 2):
                        row_ab = pair_stats_df[
                            (pair_stats_df["card_a"] == a) & (pair_stats_df["card_b"] == b)
                        ]
                        if row_ab.empty:
                            row_ab = pair_stats_df[
                                (pair_stats_df["card_a"] == b) & (pair_stats_df["card_b"] == a)
                            ]
                        if not row_ab.empty:
                            r = row_ab.iloc[0]
                            pair_rows.append({
                                "Pair": f"{a} + {b}",
                                "Co-appearances": int(r["co_appearances"]),
                                "Wins Together": int(r["wins_together"]),
                                "Pair Win Rate %": round(float(r["win_rate_together"]) * 100, 2),
                            })
                        else:
                            pair_rows.append({
                                "Pair": f"{a} + {b}",
                                "Co-appearances": 0,
                                "Wins Together": 0,
                                "Pair Win Rate %": None,
                            })
                    if pair_rows:
                        pair_tbl = pd.DataFrame(pair_rows).sort_values("Pair Win Rate %", ascending=False)
                        st.dataframe(pair_tbl, use_container_width=True, hide_index=True)

    elif len(combo_picks) == 1:
        st.caption("Add at least one more card to see combination stats.")

elif page == "Rarity & Pay-to-Win":
    st.title("💎 Rarity & Pay-to-Win Investigation")
    st.caption("Rarity vs win rate (same Season 18 sample).")

    rarity_order = ["Common", "Rare", "Epic", "Legendary"]
    cs = card_stats[card_stats["rarity"].isin(rarity_order)].copy()
    cs["rarity"] = pd.Categorical(cs["rarity"], categories=rarity_order, ordered=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Win Rate Distribution by Rarity")
        box = alt.Chart(cs).mark_boxplot(extent="min-max", size=40).encode(
            x=alt.X("rarity:N", sort=rarity_order, title="Rarity"), y=alt.Y("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")), color=rarity_color_scale(),
            tooltip=[alt.Tooltip("card_name:N", title="Card"), alt.Tooltip("win_rate:Q", format=".1%")],
        ).properties(height=400)
        pts = alt.Chart(cs).mark_circle(opacity=0.6, size=60).encode(
            x=alt.X("rarity:N", sort=rarity_order), y=alt.Y("win_rate:Q", axis=alt.Axis(format=".1%")), color=rarity_color_scale(),
            tooltip=[alt.Tooltip("card_name:N", title="Card"), alt.Tooltip("win_rate:Q", format=".1%")],
        )
        st.altair_chart(box + pts + hline(0.5), use_container_width=True)

    with col2:
        st.subheader("Avg Win Rate & Card Count by Rarity")
        rs = rarity_stats[rarity_stats["rarity"].isin(rarity_order)].copy()
        rs["rarity"] = pd.Categorical(rs["rarity"], categories=rarity_order, ordered=True)
        rs = rs.sort_values("rarity")

        bars_rs = alt.Chart(rs).mark_bar(opacity=0.85).encode(
            x=alt.X("rarity:N", sort=rarity_order, title="Rarity"), y=alt.Y("avg_win_rate:Q", title="Avg Win Rate", axis=alt.Axis(format=".1%")), color=rarity_color_scale(),
            tooltip=[alt.Tooltip("rarity:N", title="Rarity"), alt.Tooltip("avg_win_rate:Q", title="Avg Win Rate", format=".1%"), alt.Tooltip("num_cards:Q", title="# Cards")],
        )
        line_rs = alt.Chart(rs).mark_line(point=True, color="white", strokeDash=[4, 2]).encode(
            x=alt.X("rarity:N", sort=rarity_order), y=alt.Y("num_cards:Q", title="# Cards", axis=alt.Axis(titleColor="white")),
            tooltip=[alt.Tooltip("num_cards:Q", title="# Cards")],
        )
        dual = alt.layer(bars_rs, line_rs).resolve_scale(y="independent").properties(height=400)
        st.altair_chart(dual, use_container_width=True)

    st.subheader("Elixir Cost vs Win Rate")
    cs_valid = cs[cs["elixir_cost"] > 0].copy()
    x_vals = cs_valid["elixir_cost"].values.astype(float)
    y_vals = cs_valid["win_rate"].values
    coeffs = np.polyfit(x_vals, y_vals, 1)
    trend_df = pd.DataFrame({
        "elixir_cost": np.linspace(x_vals.min(), x_vals.max(), 80),
    })
    trend_df["win_rate"] = np.polyval(coeffs, trend_df["elixir_cost"])

    scatter_ec = alt.Chart(cs_valid).mark_circle(opacity=0.85).encode(
        x=alt.X("elixir_cost:Q", title="Elixir Cost", scale=alt.Scale(domain=[0, 10])), y=alt.Y("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")), color=rarity_color_scale(),
        size=alt.Size("total_appearances:Q", scale=alt.Scale(range=[40, 600]), legend=None),
        tooltip=[alt.Tooltip("card_name:N", title="Card"), alt.Tooltip("rarity:N", title="Rarity"), alt.Tooltip("elixir_cost:Q", title="Elixir"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%")],
    )
    trend_line = alt.Chart(trend_df).mark_line(color="white", strokeDash=[6, 3], strokeWidth=2).encode(
        x="elixir_cost:Q", y="win_rate:Q", tooltip=[alt.Tooltip("win_rate:Q", title=f"Trend (slope={coeffs[0]:+.4f})", format=".3f")],
    )
    st.altair_chart((scatter_ec + trend_line + hline(0.5)).properties(height=420).interactive(), use_container_width=True)

    st.subheader("Best Legendary Cards vs Best Common Cards")
    col_leg, col_com = st.columns(2)
    top_leg = cs[cs["rarity"] == "Legendary"].nlargest(5, "win_rate")
    top_com = cs[cs["rarity"] == "Common"].nlargest(5, "win_rate")

    with col_leg:
        st.markdown("**Top 5 Legendary Cards by Win Rate**")
        img_cols = st.columns(5)
        for i, (_, row) in enumerate(top_leg.iterrows()):
            with img_cols[i]:
                st.image(card_image_url(row["card_name"]), width=60)
                st.markdown(f"<div style='text-align:center;font-size:0.7rem'>{row['card_name']}<br><b>{row['win_rate']:.1%}</b></div>", unsafe_allow_html=True)
    with col_com:
        st.markdown("**Top 5 Common Cards by Win Rate**")
        img_cols2 = st.columns(5)
        for i, (_, row) in enumerate(top_com.iterrows()):
            with img_cols2[i]:
                st.image(card_image_url(row["card_name"]), width=60)
                st.markdown(f"<div style='text-align:center;font-size:0.7rem'>{row['card_name']}<br><b>{row['win_rate']:.1%}</b></div>", unsafe_allow_html=True)

    st.subheader("Rarity Summary Statistics")
    rs_disp = rs[["rarity","avg_win_rate","median_win_rate","num_cards","total_appearances"]].copy()
    rs_disp["avg_win_rate"]    = (rs_disp["avg_win_rate"]    * 100).round(2)
    rs_disp["median_win_rate"] = (rs_disp["median_win_rate"] * 100).round(2)
    rs_disp.columns = ["Rarity","Avg Win Rate %","Median Win Rate %","# Cards","Total Appearances"]
    st.dataframe(rs_disp, use_container_width=True, hide_index=True)

elif page == "Card Level Impact":
    st.title("📈 Card Level Impact Analysis")
    st.caption("Winner vs loser average card level delta vs win rate.")

    level_plot = level_adv.dropna(subset=["level_bin_mid", "win_rate"])
    level_plot = level_plot[level_plot["count"] > 50].copy()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Win Probability vs Level Advantage")
        line_lv = alt.Chart(level_plot).mark_line(point=True, color="#4FC3F7", strokeWidth=2).encode(
            x=alt.X("level_bin_mid:Q", title="Avg Card Level Advantage"), y=alt.Y("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")),
            tooltip=[alt.Tooltip("level_bin_mid:Q", title="Level Advantage"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%"), alt.Tooltip("count:Q", title="# Battles")],
        ).properties(height=380)
        st.altair_chart(line_lv + hline(0.5) + vline(0.0), use_container_width=True)

    with col2:
        st.subheader("Battle Volume by Level Advantage (winner ≥ 0)")
        pos = level_plot[level_plot["level_bin_mid"] >= 0].copy()
        bar_lv = alt.Chart(pos).mark_bar().encode(
            x=alt.X("level_bin_mid:Q", title="Level Advantage", bin=False), y=alt.Y("count:Q", title="# Battles"),
            color=alt.Color("win_rate:Q", scale=alt.Scale(scheme="redyellowgreen", domain=[0.45, 0.65]), legend=alt.Legend(title="Win Rate", format=".0%")),
            tooltip=[alt.Tooltip("level_bin_mid:Q", title="Level Advantage"), alt.Tooltip("count:Q", title="# Battles"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%")],
        ).properties(height=380)
        st.altair_chart(bar_lv, use_container_width=True)

    st.subheader("Avg Level Disparity by Trophy Range")
    st.caption("Mean |level diff| per card by trophy band.")
    tl = trophy_level.dropna().copy()
    bar_tr = alt.Chart(tl).mark_bar().encode(
        x=alt.X("trophy_range:N", title="Trophy Range", sort=None), y=alt.Y("avg_level_diff:Q", title="Avg |Level Diff| per Card"),
        color=alt.Color("avg_level_diff:Q", scale=alt.Scale(scheme="redyellowgreen", reverse=True), legend=None),
        tooltip=[alt.Tooltip("trophy_range:N", title="Trophy Range"), alt.Tooltip("avg_level_diff:Q", title="Avg Level Diff", format=".3f"), alt.Tooltip("battle_count:Q", title="Battles")],
    ).properties(height=360)
    text_tr = bar_tr.mark_text(dy=-8, color="white").encode(
        text=alt.Text("avg_level_diff:Q", format=".2f")
    )
    st.altair_chart(bar_tr + text_tr, use_container_width=True)

    above = level_plot[level_plot["level_bin_mid"] > 0]
    if not above.empty:
        best = above.nlargest(1, "win_rate").iloc[0]
        st.caption(f"Largest positive bin: +{best['level_bin_mid']:.1f} level edge → {best['win_rate']:.1%} win rate.")

elif page == "Deck Cost Analysis":
    st.title("💰 Deck Cost Analysis")
    st.caption("Deck average elixir vs volume and win rate.")

    dc = deck_cost.dropna(subset=["cost_bin_mid", "win_rate"])
    dc = dc[dc["count"] > 100].copy()

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Win Rate & Battle Volume vs Avg Deck Elixir")
        bars_dc = alt.Chart(dc).mark_bar(opacity=0.4, color="#4FC3F7").encode(
            x=alt.X("cost_bin_mid:Q", title="Average Deck Elixir Cost"), y=alt.Y("count:Q", title="Battle Count"),
            tooltip=[alt.Tooltip("cost_bin_mid:Q", title="Avg Elixir"), alt.Tooltip("count:Q", title="Battles")],
        )
        line_dc = alt.Chart(dc).mark_line(color="#FFD700", strokeWidth=3, point=alt.OverlayMarkDef(color="#FFD700", size=60)).encode(
            x=alt.X("cost_bin_mid:Q"), y=alt.Y("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")),
            tooltip=[alt.Tooltip("cost_bin_mid:Q", title="Avg Elixir"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%")],
        )
        dual_dc = alt.layer(bars_dc, line_dc + hline(0.5)).resolve_scale(y="independent").properties(height=440)
        st.altair_chart(dual_dc, use_container_width=True)

    with col2:
        st.subheader("Stats by Cost Bin")
        disp = dc[["cost_bin_mid", "count", "win_rate"]].copy()
        disp["win_rate"] = (disp["win_rate"] * 100).round(2)
        disp.columns = ["Avg Elixir", "Battles", "Win Rate %"]
        st.dataframe(disp, use_container_width=True, height=440, hide_index=True)

    st.subheader("Card Usage & Win Rate by Elixir Cost")
    cs_e = card_stats[card_stats["elixir_cost"] > 0].copy()
    eu   = cs_e.groupby("elixir_cost").agg(
        total_appearances=("total_appearances", "sum"),
        avg_win_rate=("win_rate", "mean"),
    ).reset_index()

    bars_eu = alt.Chart(eu).mark_bar(opacity=0.5, color="#4FC3F7").encode(
        x=alt.X("elixir_cost:O", title="Elixir Cost"), y=alt.Y("total_appearances:Q", title="Total Appearances"),
        tooltip=[alt.Tooltip("elixir_cost:O", title="Elixir"), alt.Tooltip("total_appearances:Q", title="Appearances")],
    )
    line_eu = alt.Chart(eu).mark_line(color="#FFD700", strokeWidth=3, point=alt.OverlayMarkDef(color="#FFD700", size=70)).encode(
        x=alt.X("elixir_cost:O"), y=alt.Y("avg_win_rate:Q", title="Avg Win Rate", axis=alt.Axis(format=".1%")),
        tooltip=[alt.Tooltip("elixir_cost:O", title="Elixir"), alt.Tooltip("avg_win_rate:Q", title="Avg Win Rate", format=".1%")],
    )
    dual_eu = alt.layer(bars_eu, line_eu).resolve_scale(y="independent").properties(height=380)
    st.altair_chart(dual_eu, use_container_width=True)

elif page == "Deck Builder":
    from streamlit_clickable_images import clickable_images

    st.title("🛠️ Deck Builder & Analyzer")
    st.caption("Pool: click to add. Slots: remove. Max 8, no dupes.")

    named_cards = card_stats[~card_stats["card_name"].str.startswith("Card_")].copy()
    named_cards = named_cards.sort_values("total_appearances", ascending=False)

    if "deck"            not in st.session_state: st.session_state.deck            = []
    if "last_pool_click" not in st.session_state: st.session_state.last_pool_click = -1
    if "last_deck_click" not in st.session_state: st.session_state.last_deck_click = -1

    deck   = st.session_state.deck
    filled = len(deck)

    st.markdown("### Your Deck")
    _deck_status = "8/8" if filled == 8 else f"{filled}/8"
    st.markdown(f"<p class='deck-progress'>{_deck_status}</p>", unsafe_allow_html=True)

    slot_cols = st.columns(8)
    for i in range(8):
        with slot_cols[i]:
            if i < filled:
                cname    = deck[i]
                row_data = named_cards[named_cards["card_name"] == cname]
                rarity   = row_data["rarity"].iloc[0]   if not row_data.empty else "Unknown"
                elixir   = row_data["elixir_cost"].iloc[0] if not row_data.empty else 0
                rc       = RARITY_COLORS.get(rarity, "#aaa")
                st.image(card_image_url(cname), use_container_width=True)
                st.markdown(f"<div class='card-meta-tiny'><span style='color:{rc}'>■</span> {cname}<br>⚡{int(elixir)}</div>", unsafe_allow_html=True)
                if st.button("✕ Remove", key=f"remove_{i}", help=f"Remove {cname}", use_container_width=True):
                    st.session_state.deck.pop(i)
                    st.session_state.last_pool_click = -1
                    st.rerun()
            else:
                st.markdown("<div class='deck-slot-empty'>+</div><div class='deck-slot-empty-label'>empty</div>", unsafe_allow_html=True)

    clear_col, _ = st.columns([1, 5])
    with clear_col:
        if st.button("🗑️ Clear Deck", type="secondary", disabled=(filled == 0)):
            st.session_state.deck            = []
            st.session_state.last_pool_click = -1
            st.session_state.last_deck_click = -1
            st.rerun()

    st.markdown("---")

    st.markdown("### Card Pool")
    st.caption("In-deck cards omitted from the pool.")

    fcol1, fcol2, fcol3 = st.columns([3, 2, 2])
    with fcol1:
        search = st.text_input("search", placeholder="Search…", label_visibility="collapsed")
    with fcol2:
        rarity_pool_filter = st.multiselect("Rarity", ["Common", "Rare", "Epic", "Legendary"], default=["Common", "Rare", "Epic", "Legendary"], label_visibility="collapsed")
    with fcol3:
        sort_by = st.selectbox("Sort", ["Popularity", "Win Rate", "Elixir Cost", "Name"], label_visibility="collapsed")

    pool = named_cards[
        named_cards["rarity"].isin(rarity_pool_filter) &
        ~named_cards["card_name"].isin(deck)
    ].copy()
    if search.strip():
        pool = pool[pool["card_name"].str.contains(search.strip(), case=False, na=False)]

    sort_map = {
        "Popularity":  ("total_appearances", False),
        "Win Rate":    ("win_rate",           False),
        "Elixir Cost": ("elixir_cost",        True),
        "Name":        ("card_name",          True),
    }
    _sc, _sa = sort_map[sort_by]
    pool      = pool.sort_values(_sc, ascending=_sa)
    pool_list = pool.to_dict("records")

    _pool_sig = (
        sort_by,
        search.strip(),
        tuple(sorted(rarity_pool_filter)),
        tuple(st.session_state.deck),
    )
    if st.session_state.get("_deck_pool_sig") != _pool_sig:
        st.session_state._deck_pool_sig = _pool_sig
        st.session_state.last_pool_click = -1
    _pool_images_key = hashlib.md5(repr(_pool_sig).encode("utf-8")).hexdigest()[:20]

    if not pool_list:
        if filled == 8:
            st.caption("Deck full — remove a card to change the pool.")
        else:
            st.caption("No matches for current filters.")
    else:
        pool_urls   = [card_image_url(r["card_name"]) for r in pool_list]
        pool_titles = [
            f"➕ {r['card_name']} · ⚡{int(r['elixir_cost'])} · {r['win_rate']:.1%} WR"
            for r in pool_list
        ]
        pool_clicked = clickable_images(
            pool_urls, titles=pool_titles, key=f"pool_images_{_pool_images_key}",
            div_style={"display": "flex", "flex-wrap": "wrap", "gap": "6px", "padding": "10px", "background": "rgba(255,255,255,0.02)", "border-radius": "12px", "border": "1px solid rgba(255,255,255,0.06)", "max-height": "520px", "overflow-y": "auto"},
            img_style={"width": "72px", "height": "86px", "object-fit": "contain", "border-radius": "8px", "cursor": "pointer" if filled < 8 else "not-allowed", "border": "2px solid rgba(255,255,255,0.1)", "transition": "transform 0.15s, border-color 0.15s", "opacity": "1" if filled < 8 else "0.4"},
        )
        if pool_clicked != st.session_state.last_pool_click and pool_clicked >= 0:
            st.session_state.last_pool_click = pool_clicked
            if filled < 8 and pool_clicked < len(pool_list):
                chosen = pool_list[pool_clicked]["card_name"]
                if chosen not in st.session_state.deck:
                    st.session_state.deck.append(chosen)
                    st.rerun()

        if filled < 8:
            st.caption(f"{len(pool_list)} cards")
        else:
            st.caption("Deck full")

    if deck:
        st.markdown("---")
        st.markdown("### Deck Analysis")

        deck_rows = []
        for cname in deck:
            r = named_cards[named_cards["card_name"] == cname]
            if not r.empty:
                ri = r.iloc[0]
                deck_rows.append({
                    "card_name":       cname,
                    "rarity":          ri["rarity"],
                    "elixir_cost":     ri["elixir_cost"],
                    "win_rate":        ri["win_rate"],
                    "appearance_rate": ri["appearance_rate"],
                    "card_type":       ri.get("card_type", "Troop"),
                })

        if deck_rows:
            deck_df     = pd.DataFrame(deck_rows)
            avg_elixir  = deck_df["elixir_cost"].mean()
            avg_wr      = deck_df["win_rate"].mean()
            rarity_counts = deck_df["rarity"].value_counts()
            type_counts   = deck_df["card_type"].value_counts()
            n_troops      = int(type_counts.get("Troop", 0))
            n_spells      = int(type_counts.get("Spell", 0))
            n_buildings   = int(type_counts.get("Building", 0))
            if n_buildings >= 2 and avg_elixir >= 3.8:
                archetype = "Siege"
            elif n_spells >= 3 and avg_elixir < 3.8:
                archetype = "Control"
            elif avg_elixir >= 4.0:
                archetype = "Beatdown"
            elif avg_elixir < 3.2:
                archetype = "Cycle"
            else:
                archetype = "Midrange"

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Avg Elixir Cost",    f"{avg_elixir:.2f}")
            m2.metric("Avg Card Win Rate",  f"{avg_wr:.1%}")
            m3.metric("Deck Archetype",     archetype)
            m4.metric("Cards Selected",     f"{len(deck)} / 8")

            if len(deck) == 8:
                col_a, col_b = st.columns(2)

                with col_a:
                    st.subheader("Elixir Cost per Card")
                    avg_line = pd.DataFrame({"y": [avg_elixir]})
                    bar_deck = alt.Chart(deck_df).mark_bar().encode(
                        x=alt.X("card_name:N", sort=None, title="", axis=alt.Axis(labelAngle=-30)), y=alt.Y("elixir_cost:Q", title="Elixir Cost"), color=rarity_color_scale(),
                        tooltip=[alt.Tooltip("card_name:N", title="Card"), alt.Tooltip("elixir_cost:Q", title="Elixir")],
                    )
                    avg_rule = alt.Chart(avg_line).mark_rule(strokeDash=[5, 3], color="#FFD700", strokeWidth=2).encode(y="y:Q")
                    st.altair_chart((bar_deck + avg_rule).properties(height=300), use_container_width=True)

                with col_b:
                    st.subheader("Win Rate per Card")
                    bar_wr = alt.Chart(deck_df.sort_values("win_rate")).mark_bar().encode(
                        x=alt.X("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%")), y=alt.Y("card_name:N", sort="x", title=""), color=rarity_color_scale(),
                        tooltip=[alt.Tooltip("card_name:N", title="Card"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%")],
                    ).properties(height=300)
                    st.altair_chart(bar_wr + hline(0.5), use_container_width=True)

                col_pie, col_tip = st.columns([1, 1])
                with col_pie:
                    st.subheader("Rarity Breakdown")
                    rc_df = rarity_counts.reset_index()
                    rc_df.columns = ["Rarity", "Count"]
                    pie = alt.Chart(rc_df).mark_arc(innerRadius=50).encode(
                        theta=alt.Theta("Count:Q"), color=alt.Color("Rarity:N", scale=alt.Scale(domain=RARITY_DOMAIN, range=RARITY_RANGE)),
                        tooltip=[alt.Tooltip("Rarity:N", title="Rarity"), alt.Tooltip("Count:Q", title="Cards")],
                    ).properties(height=280)
                    st.altair_chart(pie, use_container_width=True)

                with col_tip:
                    st.subheader("Deck Verdict")
                    archetype_desc = {
                        "Cycle":    "**Cycle** — low avg elixir, cheap rotation.",
                        "Midrange": "**Midrange** — mid elixir, mixed roles.",
                        "Beatdown": "**Beatdown** — high elixir, big pushes.",
                        "Siege":    "**Siege** — multiple buildings, higher elixir.",
                        "Control":  "**Control** — spell-heavy, lower elixir.",
                    }
                    st.markdown(archetype_desc.get(archetype, archetype))
                    if avg_wr > 0.51:
                        st.caption(f"Mean card WR in deck: {avg_wr:.1%} (above ~50%).")
                    elif avg_wr < 0.49:
                        st.caption(f"Mean card WR in deck: {avg_wr:.1%} (below ~50%).")
                    else:
                        st.caption(f"Mean card WR in deck: {avg_wr:.1%}.")

                st.markdown("---")
                st.subheader("Card Type Composition")
                tc1, tc2, tc3, _ = st.columns(4)
                tc1.metric("Troops",    n_troops,    help="Main combat units (troops / champions)")
                tc2.metric("Spells",    n_spells,    help="Direct damage and utility spells")
                tc3.metric("Buildings", n_buildings, help="Defensive structures and spawners")
                if n_spells == 0:
                    st.caption("0 spells in deck.")
                elif n_spells > 3:
                    st.caption(f"{n_spells} spells — high spell count.")

                st.subheader("Your Deck on the Meta Win Rate Curve")
                st.caption("Season 18 win rate by deck avg elixir; marker = this deck's cost bin.")
                curve_df = deck_cost[
                    (deck_cost["cost_bin_mid"] >= 2.0) &
                    (deck_cost["cost_bin_mid"] <= 5.5) &
                    (deck_cost["count"] > 1000)
                ].copy()
                closest_idx = (curve_df["cost_bin_mid"] - avg_elixir).abs().argsort()
                expected_wr = float(curve_df.iloc[closest_idx.iloc[0]]["win_rate"]) if not curve_df.empty else 0.5

                area_curve = alt.Chart(curve_df).mark_area(color="#4FC3F7", opacity=0.15).encode(
                    x=alt.X("cost_bin_mid:Q", title="Average Deck Elixir Cost", scale=alt.Scale(domain=[2.0, 5.5])),
                    y=alt.Y("win_rate:Q", title="Win Rate", axis=alt.Axis(format=".1%"), scale=alt.Scale(domain=[0.3, 0.70])),
                )
                line_curve = alt.Chart(curve_df).mark_line(color="#4FC3F7", strokeWidth=2.5).encode(
                    x=alt.X("cost_bin_mid:Q", scale=alt.Scale(domain=[2.0, 5.5])), y=alt.Y("win_rate:Q", axis=alt.Axis(format=".1%"), scale=alt.Scale(domain=[0.3, 0.70])),
                    tooltip=[alt.Tooltip("cost_bin_mid:Q", title="Avg Elixir", format=".2f"), alt.Tooltip("win_rate:Q", title="Win Rate", format=".1%"), alt.Tooltip("count:Q", title="Battles")],
                )
                deck_pt_df = pd.DataFrame({"x": [avg_elixir], "y": [expected_wr]})
                deck_point = alt.Chart(deck_pt_df).mark_point(size=200, color="#FFD700", shape="triangle-up", filled=True).encode(
                    x=alt.X("x:Q", axis=None), y=alt.Y("y:Q", axis=None),
                    tooltip=[alt.Tooltip("x:Q", title="Your Avg Elixir", format=".2f"), alt.Tooltip("y:Q", title="Expected WR", format=".1%")],
                )
                st.altair_chart((area_curve + line_curve + hline(0.5) + vline(avg_elixir, color="#FFD700") + deck_point).properties(height=280), use_container_width=True)
                st.caption(f"Avg elixir {avg_elixir:.2f}; bin WR ≈ {expected_wr:.1%}.")

                st.subheader("Swap Suggestions")

                _pair_stats = load_card_pair_stats()

                def _card_synergy_score(card_name, others, pair_df, card_df):
                    row = card_df[card_df["card_name"] == card_name]
                    indiv_wr = float(row["win_rate"].iloc[0]) if not row.empty else 0.5
                    if pair_df is None or not others:
                        return indiv_wr
                    pair_wrs = []
                    for other in others:
                        a, b = sorted([card_name, other])
                        pr = pair_df[(pair_df["card_a"] == a) & (pair_df["card_b"] == b)]
                        if not pr.empty:
                            pair_wrs.append(float(pr.iloc[0]["win_rate_together"]))
                    pair_score = float(np.mean(pair_wrs)) if pair_wrs else indiv_wr
                    return 0.6 * pair_score + 0.4 * indiv_wr

                deck_scores = {}
                for cname in deck:
                    others = [c for c in deck if c != cname]
                    deck_scores[cname] = _card_synergy_score(cname, others, _pair_stats, named_cards)

                min_app_thresh = float(named_cards["total_appearances"].quantile(0.25))
                swap_pool = named_cards[
                    (named_cards["total_appearances"] >= min_app_thresh) &
                    (~named_cards["card_name"].isin(deck))
                ].copy()

                deck_type_counts = deck_df["card_type"].value_counts().to_dict()

                ranked_weak = sorted(deck_scores.items(), key=lambda x: x[1])[:3]

                any_suggestion = False
                for w_name, w_score in ranked_weak:
                    w_row    = deck_df[deck_df["card_name"] == w_name].iloc[0]
                    w_elixir = w_row["elixir_cost"]
                    w_wr     = w_row["win_rate"]
                    w_rarity = w_row["rarity"]
                    w_type   = w_row["card_type"]
                    others   = [c for c in deck if c != w_name]

                    scored_alts = []
                    for _, alt in swap_pool.iterrows():
                        alt_name = alt["card_name"]
                        alt_score = _card_synergy_score(alt_name, others, _pair_stats, named_cards)
                        improvement = alt_score - w_score
                        if improvement <= 0:
                            continue
                        elixir_delta = int(alt["elixir_cost"]) - int(w_elixir)

                        elixir_penalty = abs(elixir_delta) * 0.005
                        net = improvement - elixir_penalty

                        sole_type = (deck_type_counts.get(w_type, 0) == 1)
                        type_ok   = (not sole_type) or (alt["card_type"] == w_type)
                        scored_alts.append((net, alt_score, alt, elixir_delta, type_ok))

                    if not scored_alts:
                        continue

                    scored_alts.sort(key=lambda x: (not x[4], -x[0]))
                    top_alts = scored_alts[:3]

                    any_suggestion = True
                    n_alts = len(top_alts)
                    rc = RARITY_COLORS.get(w_rarity, "#aaa")

                    label_col, weak_col, arrow_col, *alt_cols = st.columns([0.55, 1, 0.3] + [1] * n_alts)
                    with label_col:
                        st.markdown("<div class='swap-remove-badge-wrap'><span class='swap-remove-badge'>REMOVE</span></div>", unsafe_allow_html=True)
                    with weak_col:
                        st.image(card_image_url(w_name), use_container_width=True)
                        st.markdown(
                            f"<div class='swap-card-meta'><b>{w_name}</b><br>"
                            f"<span style='color:{rc}'>■</span> {w_rarity}<br>"
                            f"⚡{int(w_elixir)} &nbsp;·&nbsp; <span style='color:#ff6b6b'>WR {w_wr:.1%}</span><br>"
                            f"<span style='color:#aaa;font-size:0.6rem'>deck score {w_score:.3f}</span></div>",
                            unsafe_allow_html=True,
                        )
                    with arrow_col:
                        st.markdown("<div class='swap-arrow'>→</div>", unsafe_allow_html=True)

                    for _, (net, alt_score, alt_row, elixir_delta, type_ok) in enumerate(top_alts):
                        with alt_cols[_]:
                            wr_delta   = (alt_row["win_rate"] - w_wr) * 100
                            rc_a       = RARITY_COLORS.get(alt_row["rarity"], "#aaa")
                            elixir_tag = (f"<span style='color:#ff9800'>⚡{int(alt_row['elixir_cost'])} ({elixir_delta:+d})</span>"
                                          if elixir_delta != 0
                                          else f"⚡{int(alt_row['elixir_cost'])}")
                            warn_tag   = "" if type_ok else "<br><span style='color:#ff9800;font-size:0.58rem'>⚠ lone type</span>"
                            st.image(card_image_url(alt_row["card_name"]), use_container_width=True)
                            st.markdown(
                                f"<div class='swap-card-meta'><b>{alt_row['card_name']}</b><br>"
                                f"<span style='color:{rc_a}'>■</span> {alt_row['rarity']}<br>"
                                f"{elixir_tag} &nbsp;·&nbsp; <span style='color:#4caf50'>+{wr_delta:.1f}%</span><br>"
                                f"<span style='color:#aaa;font-size:0.6rem'>deck score {alt_score:.3f}{warn_tag}</span></div>",
                                unsafe_allow_html=True,
                            )
                    st.markdown("<hr class='hr-soft'>", unsafe_allow_html=True)

                if not any_suggestion:
                    st.caption("No improvements found — your deck looks well-optimised for this meta.")
                else:
                    use_pair = _pair_stats is not None
                    st.caption(
                        "Ranked by deck synergy score (pair win-rate with remaining 7 cards + individual WR)."
                        if use_pair else
                        "Ranked by individual win rate (run preprocess.py to unlock synergy scoring)."
                    )

                st.markdown("---")
                st.subheader("Biggest Threats to Your Deck")
                _counter_path = os.path.join(PROCESSED_DIR, "counter_matrix.parquet")
                if os.path.exists(_counter_path):
                    @st.cache_data
                    def _load_counter():
                        return pd.read_parquet(_counter_path)

                    counter_df = _load_counter()
                    deck_set   = set(deck)
                    threats = counter_df[
                        (~counter_df["card_a"].isin(deck_set)) &
                        (counter_df["card_b"].isin(deck_set)) &
                        (~counter_df["card_a"].str.startswith("Card_"))
                    ].copy()

                    if not threats.empty:
                        threat_scores = threats.groupby("card_a").agg(counter_score=("win_rate", "mean"), coverage=("card_b", "count")).reset_index().sort_values("counter_score", ascending=False).head(5)
                        st.caption("Head-to-head: attackers not in your deck vs your cards.")
                        threat_cols = st.columns(len(threat_scores))
                        for t_idx, (_, trow) in enumerate(threat_scores.iterrows()):
                            with threat_cols[t_idx]:
                                t_meta = named_cards[named_cards["card_name"] == trow["card_a"]]
                                t_rar  = t_meta["rarity"].iloc[0]    if not t_meta.empty else "Unknown"
                                t_eli  = t_meta["elixir_cost"].iloc[0] if not t_meta.empty else 0
                                t_rc   = RARITY_COLORS.get(t_rar, "#aaa")
                                st.image(card_image_url(trow["card_a"]), use_container_width=True)
                                st.markdown(f"<div class='threat-card-meta'><b>{trow['card_a']}</b><br><span style='color:{t_rc}'>■</span> {t_rar} · ⚡{int(t_eli)}<br><span style='color:#ff6b6b;font-weight:700'>{trow['counter_score']:.1%} WR</span><br><span style='color:#aaa;font-size:0.6rem'>covers {int(trow['coverage'])} deck cards</span></div>", unsafe_allow_html=True)
            else:
                st.caption(f"{8 - len(deck)} more cards for full analysis.")
