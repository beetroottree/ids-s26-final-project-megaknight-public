"""
Clash Royale Meta Analyzer — Streamlit Dashboard
Team: Nihar Atri, Hou Kin Wan, Andrew Zhang, Natan Zmudzinski
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clash Royale Meta Analyzer",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Sidebar background */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
}
[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}

/* Nav buttons */
div[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    color: #e0e0e0 !important;
    padding: 0.5rem 1rem;
    margin-bottom: 4px;
    font-size: 0.92rem;
    transition: background 0.2s;
}
div[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,165,0,0.2);
    border-color: rgba(255,165,0,0.5);
}

/* Active page button */
div[data-testid="stSidebar"] .active-btn button {
    background: rgba(255,165,0,0.3) !important;
    border-color: #ffa500 !important;
    color: #ffd700 !important;
    font-weight: 600;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 0.8rem 1rem;
}

/* Main background */
.main .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

PROCESSED_DIR = "data/processed"

RARITY_COLORS = {
    "Common": "#9E9E9E",
    "Rare": "#4FC3F7",
    "Epic": "#CE93D8",
    "Legendary": "#FFD54F",
    "Unknown": "#78909C",
}

# Card image URL helper
def card_image_url(card_name: str) -> str:
    slug = (
        card_name.lower()
        .replace("p.e.k.k.a.", "pekka")
        .replace("mini p.e.k.k.a.", "mini-pekka")
        .replace(".", "")
        .replace(" ", "-")
        .replace("--", "-")
    )
    return f"https://raw.githubusercontent.com/martincarrera/clash-royale-api/master/public/images/cards/{slug}.png"

PAGES = [
    ("🏠", "Overview"),
    ("🃏", "Card Stats"),
    ("💎", "Rarity & Pay-to-Win"),
    ("📈", "Card Level Impact"),
    ("💰", "Deck Cost Analysis"),
    ("🛠️", "Deck Builder"),
]

# ── Session state for page ─────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "Overview"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='text-align:center;color:#ffd700;margin-bottom:0'>⚔️ Clash Royale</h2>"
        "<p style='text-align:center;color:#aaa;margin-top:2px;font-size:0.85rem'>Meta Analyzer</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("<p style='color:#aaa;font-size:0.75rem;margin-bottom:6px'>NAVIGATION</p>", unsafe_allow_html=True)

    for icon, name in PAGES:
        is_active = st.session_state.page == name
        container = st.container()
        if is_active:
            container.markdown('<div class="active-btn">', unsafe_allow_html=True)
        if container.button(f"{icon}  {name}", key=f"nav_{name}"):
            st.session_state.page = name
            st.rerun()
        if is_active:
            container.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "<p style='color:#aaa;font-size:0.75rem'>📅 Season 18 · Dec 2020<br>"
        "⚔️ ~6.8M battles analyzed<br>"
        "🃏 102 unique cards</p>",
        unsafe_allow_html=True,
    )

page = st.session_state.page

# ── Data loading ───────────────────────────────────────────────────────────────
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
    return {k: pd.read_parquet(os.path.join(PROCESSED_DIR, v)) for k, v in files.items()
            if os.path.exists(os.path.join(PROCESSED_DIR, v))}


if not os.path.exists(os.path.join(PROCESSED_DIR, "card_stats.parquet")):
    st.title("⚔️ Clash Royale Meta Analyzer")
    st.warning("Run `python preprocess.py` first to generate the processed data files.")
    st.stop()

data = load_all()
card_stats = data["card_stats"]
deck_cost = data["deck_cost"]
level_adv = data["level_adv"]
rarity_stats = data["rarity_stats"]
trophy_level = data["trophy_level"]
summary = data["summary"].iloc[0]


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("⚔️ Clash Royale Meta Analyzer")
    st.markdown(
        "Explore competitive balance, card win rates, and pay-to-win dynamics across "
        "**~6.8 million Season 18 ladder battles** (December 2020)."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Battles", f"{int(summary['total_battles']):,}")
    c2.metric("Unique Cards", f"{int(summary['unique_cards'])}")
    c3.metric("Avg Trophies", f"{summary['avg_trophies']:.0f}")
    c4.metric("Date Range", "Dec 2020 – Jan 2021")

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Top 15 Most Popular Cards")
        top_pop = card_stats.nlargest(15, "total_appearances").copy()
        fig = px.bar(
            top_pop,
            x="appearance_rate", y="card_name",
            orientation="h",
            color="rarity", color_discrete_map=RARITY_COLORS,
            labels={"appearance_rate": "Appearance Rate", "card_name": ""},
            hover_data={"win_rate": ":.1%"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500, legend_title="Rarity")
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Top 15 Highest Win Rate Cards")
        min_app = card_stats["total_appearances"].quantile(0.25)
        top_wr = card_stats[card_stats["total_appearances"] >= min_app].nlargest(15, "win_rate")
        fig2 = px.bar(
            top_wr,
            x="win_rate", y="card_name",
            orientation="h",
            color="rarity", color_discrete_map=RARITY_COLORS,
            labels={"win_rate": "Win Rate", "card_name": ""},
        )
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=500, legend_title="Rarity")
        fig2.update_xaxes(tickformat=".1%", range=[0.46, 0.58])
        fig2.add_vline(x=0.5, line_dash="dash", line_color="rgba(255,255,255,0.4)")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Popularity vs Win Rate — The Meta Quadrant")
    st.caption("Top-right = popular AND effective (true meta cards). Bubble size = total appearances.")
    fig3 = px.scatter(
        card_stats,
        x="appearance_rate", y="win_rate",
        color="rarity", color_discrete_map=RARITY_COLORS,
        hover_name="card_name",
        size="total_appearances", size_max=30,
        labels={"appearance_rate": "Appearance Rate", "win_rate": "Win Rate"},
    )
    fig3.add_hline(y=0.5, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig3.add_vline(x=card_stats["appearance_rate"].median(), line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig3.update_yaxes(tickformat=".1%")
    fig3.update_xaxes(tickformat=".0%")
    fig3.update_layout(height=500)
    st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: CARD STATS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Card Stats":
    st.title("🃏 Card Popularity & Win Rates")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        rarity_filter = st.multiselect(
            "Filter by Rarity",
            options=["Common", "Rare", "Epic", "Legendary", "Unknown"],
            default=["Common", "Rare", "Epic", "Legendary"],
        )
    with col_f2:
        min_sample = st.slider("Minimum appearances (thousands)", 0, 500, 10, 10)

    filtered = card_stats[
        card_stats["rarity"].isin(rarity_filter) &
        (card_stats["total_appearances"] >= min_sample * 1000)
    ].copy()

    st.caption(f"Showing **{len(filtered)}** cards")

    # Card image grid for top cards
    st.subheader("Top Cards at a Glance")
    top_n = filtered.nlargest(16, "total_appearances")
    cols = st.columns(8)
    for i, (_, row) in enumerate(top_n.iterrows()):
        with cols[i % 8]:
            img_url = card_image_url(row["card_name"])
            st.image(img_url, caption=row["card_name"].replace(" ", "\n"), width=70)
            wr_color = "🟢" if row["win_rate"] > 0.5 else "🔴"
            st.markdown(
                f"<div style='text-align:center;font-size:0.7rem;color:#aaa'>{wr_color} {row['win_rate']:.1%}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 20 by Appearance Rate")
        fig = px.bar(
            filtered.nlargest(20, "appearance_rate"),
            x="appearance_rate", y="card_name",
            color="rarity", color_discrete_map=RARITY_COLORS,
            orientation="h",
            labels={"appearance_rate": "Appearance Rate", "card_name": ""},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
        fig.update_xaxes(tickformat=".0%")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Win Rate — Top 20 Cards by Usage")
        top20 = filtered.nlargest(20, "total_appearances").sort_values("win_rate")
        fig2 = px.bar(
            top20, x="win_rate", y="card_name",
            color="rarity", color_discrete_map=RARITY_COLORS,
            orientation="h",
            labels={"win_rate": "Win Rate", "card_name": ""},
        )
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=600)
        fig2.update_xaxes(tickformat=".1%")
        fig2.add_vline(x=0.5, line_dash="dash", line_color="rgba(255,255,255,0.4)")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Full Card Stats Table")
    display_df = filtered[["card_name","rarity","elixir_cost","total_appearances","wins","win_rate","appearance_rate"]].copy()
    display_df["win_rate"] = (display_df["win_rate"] * 100).round(2)
    display_df["appearance_rate"] = (display_df["appearance_rate"] * 100).round(2)
    display_df.columns = ["Card","Rarity","Elixir","Appearances","Wins","Win Rate %","Appearance Rate %"]
    st.dataframe(display_df.sort_values("Appearances", ascending=False), use_container_width=True, height=400)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: RARITY & PAY-TO-WIN
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Rarity & Pay-to-Win":
    st.title("💎 Rarity & Pay-to-Win Investigation")
    st.markdown(
        "Does paying for rarer (Legendary/Epic) cards actually make you win more? "
        "We test whether rarity predicts win rate across ~6.8M battles."
    )

    rarity_order = ["Common", "Rare", "Epic", "Legendary"]
    cs = card_stats[card_stats["rarity"].isin(rarity_order)].copy()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Win Rate Distribution by Rarity")
        fig = px.box(
            cs, x="rarity", y="win_rate",
            color="rarity", color_discrete_map=RARITY_COLORS,
            category_orders={"rarity": rarity_order},
            points="all", hover_name="card_name",
            labels={"win_rate": "Win Rate", "rarity": "Rarity"},
        )
        fig.add_hline(y=0.5, line_dash="dash", line_color="rgba(255,255,255,0.4)")
        fig.update_yaxes(tickformat=".1%")
        fig.update_layout(showlegend=False, height=450)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Avg Win Rate & Card Count by Rarity")
        rs = rarity_stats[rarity_stats["rarity"].isin(rarity_order)].copy()
        rs["rarity"] = pd.Categorical(rs["rarity"], categories=rarity_order, ordered=True)
        rs = rs.sort_values("rarity")

        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Bar(
            x=rs["rarity"], y=rs["avg_win_rate"],
            name="Avg Win Rate",
            marker_color=[RARITY_COLORS.get(r, "#888") for r in rs["rarity"]],
        ), secondary_y=False)
        fig2.add_trace(go.Scatter(
            x=rs["rarity"], y=rs["num_cards"],
            name="# Cards", mode="lines+markers",
            marker=dict(size=10, color="white"), line=dict(color="white", dash="dot"),
        ), secondary_y=True)
        fig2.update_yaxes(title_text="Avg Win Rate", tickformat=".1%", secondary_y=False)
        fig2.update_yaxes(title_text="Number of Cards", secondary_y=True)
        fig2.update_layout(height=450)
        st.plotly_chart(fig2, use_container_width=True)

    # Elixir cost vs win rate — manual trendline (no statsmodels)
    st.subheader("Elixir Cost vs Win Rate")
    cs_valid = cs[cs["elixir_cost"] > 0].copy()

    # Compute trendline manually
    x = cs_valid["elixir_cost"].values.astype(float)
    y = cs_valid["win_rate"].values
    coeffs = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = np.polyval(coeffs, x_line)

    fig3 = px.scatter(
        cs_valid, x="elixir_cost", y="win_rate",
        color="rarity", color_discrete_map=RARITY_COLORS,
        hover_name="card_name", size="total_appearances", size_max=25,
        labels={"elixir_cost": "Elixir Cost", "win_rate": "Win Rate"},
    )
    fig3.add_trace(go.Scatter(
        x=x_line, y=y_line, mode="lines",
        name=f"Trend (slope={coeffs[0]:+.4f})",
        line=dict(color="white", dash="dash", width=2),
    ))
    fig3.add_hline(y=0.5, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    fig3.update_yaxes(tickformat=".1%")
    fig3.update_layout(height=450)
    st.plotly_chart(fig3, use_container_width=True)

    # Best legendary vs best common
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
                st.markdown(
                    f"<div style='text-align:center;font-size:0.7rem'>{row['card_name']}<br>"
                    f"<b>{row['win_rate']:.1%}</b></div>", unsafe_allow_html=True
                )
    with col_com:
        st.markdown("**Top 5 Common Cards by Win Rate**")
        img_cols2 = st.columns(5)
        for i, (_, row) in enumerate(top_com.iterrows()):
            with img_cols2[i]:
                st.image(card_image_url(row["card_name"]), width=60)
                st.markdown(
                    f"<div style='text-align:center;font-size:0.7rem'>{row['card_name']}<br>"
                    f"<b>{row['win_rate']:.1%}</b></div>", unsafe_allow_html=True
                )

    st.subheader("Rarity Summary Statistics")
    rs_disp = rs[["rarity","avg_win_rate","median_win_rate","num_cards","total_appearances"]].copy()
    rs_disp["avg_win_rate"] = (rs_disp["avg_win_rate"] * 100).round(2)
    rs_disp["median_win_rate"] = (rs_disp["median_win_rate"] * 100).round(2)
    rs_disp.columns = ["Rarity","Avg Win Rate %","Median Win Rate %","# Cards","Total Appearances"]
    st.dataframe(rs_disp, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: CARD LEVEL IMPACT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Card Level Impact":
    st.title("📈 Card Level Impact Analysis")
    st.markdown(
        "How much does upgrading cards matter? We measure the relationship between "
        "**average card level advantage** (winner − loser, per card) and win probability."
    )

    level_plot = level_adv.dropna(subset=["level_bin_mid", "win_rate"])
    level_plot = level_plot[level_plot["count"] > 50].copy()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Win Probability vs Level Advantage")
        fig = px.line(
            level_plot, x="level_bin_mid", y="win_rate", markers=True,
            labels={"level_bin_mid": "Avg Card Level Advantage", "win_rate": "Win Rate"},
        )
        fig.add_hline(y=0.5, line_dash="dash", line_color="rgba(255,255,255,0.4)")
        fig.add_vline(x=0.0, line_dash="dash", line_color="rgba(255,255,255,0.4)")
        fig.update_yaxes(tickformat=".1%")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Battle Volume by Level Difference (winner's advantage ≥ 0)")
        pos = level_plot[level_plot["level_bin_mid"] >= 0]
        fig2 = px.bar(
            pos, x="level_bin_mid", y="count",
            color="win_rate", color_continuous_scale="RdYlGn",
            labels={"level_bin_mid": "Level Advantage", "count": "# Battles", "win_rate": "Win Rate"},
        )
        fig2.update_coloraxes(colorbar_tickformat=".0%")
        fig2.update_layout(height=420)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Avg Level Disparity by Trophy Range")
    st.caption("Does higher-skill matchmaking produce more balanced matchups?")

    tl = trophy_level.dropna().copy()
    fig3 = px.bar(
        tl, x="trophy_range", y="avg_level_diff",
        color="avg_level_diff", color_continuous_scale="RdYlGn_r",
        text=tl["avg_level_diff"].round(2),
        labels={"trophy_range": "Trophy Range", "avg_level_diff": "Avg |Level Diff| per card"},
    )
    fig3.update_traces(textposition="outside")
    fig3.update_layout(coloraxis_showscale=False, height=400)
    st.plotly_chart(fig3, use_container_width=True)

    # Key insight callout
    above = level_plot[level_plot["level_bin_mid"] > 0]
    if not above.empty:
        best = above.nlargest(1, "win_rate").iloc[0]
        st.info(
            f"**Key Finding:** Players with a +{best['level_bin_mid']:.1f} avg card level advantage "
            f"win **{best['win_rate']:.1%}** of the time — upgrades provide a real, measurable edge."
        )


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DECK COST ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Deck Cost Analysis":
    st.title("💰 Deck Cost Analysis")
    st.markdown(
        "Does average deck elixir cost predict win rate? "
        "Cheaper decks cycle faster; heavier decks hit harder."
    )

    dc = deck_cost.dropna(subset=["cost_bin_mid", "win_rate"])
    dc = dc[dc["count"] > 100].copy()

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("Win Rate & Battle Volume vs Avg Deck Elixir")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=dc["cost_bin_mid"], y=dc["count"],
            name="Battle Count",
            marker_color="rgba(79,195,247,0.35)",
        ), secondary_y=True)
        fig.add_trace(go.Scatter(
            x=dc["cost_bin_mid"], y=dc["win_rate"],
            name="Win Rate", mode="lines+markers",
            marker=dict(size=8, color="#FFD700"),
            line=dict(color="#FFD700", width=3),
        ), secondary_y=False)
        fig.add_hline(y=0.5, line_dash="dash", line_color="rgba(255,255,255,0.35)", secondary_y=False)
        fig.update_yaxes(title_text="Win Rate", tickformat=".1%", secondary_y=False)
        fig.update_yaxes(title_text="Battle Count", secondary_y=True)
        fig.update_xaxes(title_text="Average Deck Elixir Cost")
        fig.update_layout(height=480, legend=dict(x=0.02, y=0.98))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Stats by Cost Bin")
        disp = dc[["cost_bin_mid", "count", "win_rate"]].copy()
        disp["win_rate"] = (disp["win_rate"] * 100).round(2)
        disp.columns = ["Avg Elixir", "Battles", "Win Rate %"]
        st.dataframe(disp, use_container_width=True, height=480, hide_index=True)

    st.subheader("Card Usage & Win Rate by Elixir Cost")
    cs_e = card_stats[card_stats["elixir_cost"] > 0].copy()
    eu = cs_e.groupby("elixir_cost").agg(
        total_appearances=("total_appearances", "sum"),
        avg_win_rate=("win_rate", "mean"),
    ).reset_index()

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(go.Bar(
        x=eu["elixir_cost"], y=eu["total_appearances"],
        name="Total Appearances", marker_color="rgba(79,195,247,0.5)",
    ), secondary_y=False)
    fig2.add_trace(go.Scatter(
        x=eu["elixir_cost"], y=eu["avg_win_rate"],
        name="Avg Win Rate", mode="lines+markers",
        marker=dict(size=10, color="#FFD700"), line=dict(color="#FFD700", width=3),
    ), secondary_y=True)
    fig2.update_xaxes(title_text="Elixir Cost", dtick=1)
    fig2.update_yaxes(title_text="Total Appearances", secondary_y=False)
    fig2.update_yaxes(title_text="Avg Win Rate", tickformat=".1%", secondary_y=True)
    fig2.update_layout(height=400, legend=dict(x=0.02, y=0.98))
    st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE: DECK BUILDER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Deck Builder":
    st.title("🛠️ Deck Builder & Analyzer")
    st.markdown(
        "Search for cards and **click to add** them to your deck. "
        "Click a card in your deck to **remove** it. Max 8 cards, no duplicates."
    )

    # Extra CSS for the deck builder card grid
    st.markdown("""
    <style>
    /* Pool card buttons */
    .card-pool-btn button {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        width: 100% !important;
        transition: all 0.15s !important;
    }
    .card-pool-btn button:hover {
        background: rgba(255,200,0,0.18) !important;
        border-color: #ffd700 !important;
        transform: scale(1.05);
    }
    /* Deck slot buttons */
    .deck-slot-btn button {
        background: rgba(255,80,80,0.1) !important;
        border: 1px solid rgba(255,100,100,0.3) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        width: 100% !important;
    }
    .deck-slot-btn button:hover {
        background: rgba(255,60,60,0.3) !important;
        border-color: #ff4444 !important;
    }
    .empty-slot {
        border: 2px dashed rgba(255,255,255,0.15);
        border-radius: 10px;
        height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: rgba(255,255,255,0.25);
        font-size: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

    named_cards = card_stats[~card_stats["card_name"].str.startswith("Card_")].copy()
    named_cards = named_cards.sort_values("total_appearances", ascending=False)

    # ── Session state ──────────────────────────────────────────────────────────
    if "deck" not in st.session_state:
        st.session_state.deck = []  # list of card_name strings

    deck = st.session_state.deck  # shorthand

    # ── Layout: deck zone (top) + card pool (bottom) ───────────────────────────
    st.markdown("### Your Deck")
    deck_hint = f"{'▓' * len(deck)}{'░' * (8 - len(deck))}  {len(deck)}/8 cards"
    st.markdown(
        f"<p style='color:#aaa;font-size:0.85rem;margin:0 0 8px'>{deck_hint} "
        f"{'✅ Full deck!' if len(deck) == 8 else '— click cards below to add'}</p>",
        unsafe_allow_html=True,
    )

    # Render 8 deck slots (click to remove)
    slot_cols = st.columns(8)
    for i in range(8):
        with slot_cols[i]:
            if i < len(deck):
                card_name = deck[i]
                row = named_cards[named_cards["card_name"] == card_name]
                rarity = row["rarity"].iloc[0] if not row.empty else "Unknown"
                elixir = row["elixir_cost"].iloc[0] if not row.empty else 0
                wr = row["win_rate"].iloc[0] if not row.empty else 0.5
                rc = RARITY_COLORS.get(rarity, "#aaa")

                st.markdown('<div class="deck-slot-btn">', unsafe_allow_html=True)
                if st.button("✕", key=f"remove_{i}", help=f"Remove {card_name}"):
                    st.session_state.deck.pop(i)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

                st.image(card_image_url(card_name), use_container_width=True)
                st.markdown(
                    f"<div style='text-align:center;font-size:0.65rem;line-height:1.3'>"
                    f"<b>{card_name}</b><br>"
                    f"<span style='color:{rc}'>{rarity[:3]}</span> · ⚡{int(elixir)}<br>"
                    f"{'🟢' if wr > 0.5 else '🔴'} {wr:.1%}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<div class='empty-slot'>+</div>",
                    unsafe_allow_html=True,
                )

    if st.button("🗑️ Clear Deck", type="secondary"):
        st.session_state.deck = []
        st.rerun()

    st.markdown("---")

    # ── Card Pool ──────────────────────────────────────────────────────────────
    st.markdown("### Card Pool")
    st.caption("Click a card to add it to your deck. Cards already in your deck are grayed out.")

    # Filters
    fcol1, fcol2, fcol3 = st.columns([3, 2, 2])
    with fcol1:
        search = st.text_input("🔍 Search cards", placeholder="e.g. Hog, Zap, Golem...", label_visibility="collapsed")
    with fcol2:
        rarity_pool_filter = st.multiselect(
            "Rarity", ["Common", "Rare", "Epic", "Legendary"],
            default=["Common", "Rare", "Epic", "Legendary"],
            label_visibility="collapsed",
        )
    with fcol3:
        sort_by = st.selectbox("Sort by", ["Popularity", "Win Rate", "Elixir Cost", "Name"], label_visibility="collapsed")

    # Filter and sort pool
    pool = named_cards[named_cards["rarity"].isin(rarity_pool_filter)].copy()
    if search.strip():
        pool = pool[pool["card_name"].str.contains(search.strip(), case=False, na=False)]

    sort_map = {
        "Popularity": ("total_appearances", False),
        "Win Rate": ("win_rate", False),
        "Elixir Cost": ("elixir_cost", True),
        "Name": ("card_name", True),
    }
    sort_col, sort_asc = sort_map[sort_by]
    pool = pool.sort_values(sort_col, ascending=sort_asc)

    # Render pool in rows of 10
    POOL_COLS = 10
    pool_list = pool.to_dict("records")
    for row_start in range(0, len(pool_list), POOL_COLS):
        row_cards = pool_list[row_start: row_start + POOL_COLS]
        cols = st.columns(POOL_COLS)
        for j, card_row in enumerate(row_cards):
            card_name = card_row["card_name"]
            in_deck = card_name in deck
            with cols[j]:
                if in_deck:
                    # Grayed-out — already in deck
                    st.image(card_image_url(card_name), use_container_width=True)
                    st.markdown(
                        f"<div style='text-align:center;font-size:0.6rem;color:#555;line-height:1.2'>"
                        f"{card_name}<br>✓ In deck</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    # Clickable
                    st.markdown('<div class="card-pool-btn">', unsafe_allow_html=True)
                    clicked = st.button(
                        " ",
                        key=f"add_{card_name}",
                        help=f"Add {card_name} · ⚡{int(card_row['elixir_cost'])} · {card_row['win_rate']:.1%} WR",
                        disabled=(len(deck) >= 8),
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                    if clicked and card_name not in deck and len(deck) < 8:
                        st.session_state.deck.append(card_name)
                        st.rerun()
                    st.image(card_image_url(card_name), use_container_width=True)
                    st.markdown(
                        f"<div style='text-align:center;font-size:0.6rem;color:#ccc;line-height:1.2'>"
                        f"{card_name}<br>⚡{int(card_row['elixir_cost'])} · {card_row['win_rate']:.1%}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

    # ── Analysis (only when deck has ≥ 1 card) ─────────────────────────────────
    if deck:
        st.markdown("---")
        st.markdown("### Deck Analysis")

        deck_rows = []
        for card_name in deck:
            row = named_cards[named_cards["card_name"] == card_name]
            if not row.empty:
                r = row.iloc[0]
                deck_rows.append({
                    "card_name": card_name,
                    "rarity": r["rarity"],
                    "elixir_cost": r["elixir_cost"],
                    "win_rate": r["win_rate"],
                    "appearance_rate": r["appearance_rate"],
                })

        if deck_rows:
            deck_df = pd.DataFrame(deck_rows)
            avg_elixir = deck_df["elixir_cost"].mean()
            avg_wr = deck_df["win_rate"].mean()
            rarity_counts = deck_df["rarity"].value_counts()
            archetype = "Beatdown" if avg_elixir >= 4.0 else ("Cycle" if avg_elixir < 3.2 else "Midrange")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Avg Elixir Cost", f"{avg_elixir:.2f}")
            m2.metric("Avg Card Win Rate", f"{avg_wr:.1%}")
            m3.metric("Deck Archetype", archetype)
            m4.metric("Cards Selected", f"{len(deck)} / 8")

            if len(deck) == 8:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("Elixir Cost per Card")
                    fig = px.bar(
                        deck_df, x="card_name", y="elixir_cost",
                        color="rarity", color_discrete_map=RARITY_COLORS,
                        labels={"card_name": "", "elixir_cost": "Elixir Cost"},
                    )
                    fig.add_hline(y=avg_elixir, line_dash="dash", line_color="#FFD700",
                                  annotation_text=f"Avg: {avg_elixir:.2f}")
                    fig.update_layout(height=320, xaxis_tickangle=-30, showlegend=False)
                    st.plotly_chart(fig, use_container_width=True)

                with col_b:
                    st.subheader("Win Rate per Card")
                    fig2 = px.bar(
                        deck_df.sort_values("win_rate"),
                        x="win_rate", y="card_name",
                        color="rarity", color_discrete_map=RARITY_COLORS,
                        orientation="h",
                        labels={"win_rate": "Win Rate", "card_name": ""},
                    )
                    fig2.add_vline(x=0.5, line_dash="dash", line_color="rgba(255,255,255,0.4)")
                    fig2.update_xaxes(tickformat=".1%")
                    fig2.update_layout(height=320, showlegend=False)
                    st.plotly_chart(fig2, use_container_width=True)

                col_pie, col_tip = st.columns([1, 1])
                with col_pie:
                    st.subheader("Rarity Breakdown")
                    rc_df = rarity_counts.reset_index()
                    rc_df.columns = ["Rarity", "Count"]
                    fig3 = px.pie(
                        rc_df, names="Rarity", values="Count",
                        color="Rarity", color_discrete_map=RARITY_COLORS, hole=0.45,
                    )
                    fig3.update_layout(height=300)
                    st.plotly_chart(fig3, use_container_width=True)

                with col_tip:
                    st.subheader("Deck Verdict")
                    archetype_desc = {
                        "Cycle": "⚡ **Cycle Deck** — Fast and aggressive. Apply constant pressure by cycling cheap cards.",
                        "Midrange": "⚖️ **Midrange Deck** — Balanced and versatile. Adapts well to most match-ups.",
                        "Beatdown": "🐘 **Beatdown Deck** — Heavy hitters. Build up a massive push and overwhelm opponents.",
                    }
                    st.info(archetype_desc.get(archetype, ""))
                    if avg_wr > 0.51:
                        st.success(f"✅ Strong card selection — avg win rate {avg_wr:.1%}")
                    elif avg_wr < 0.49:
                        st.warning(f"⚠️ Below-average win rate cards — avg {avg_wr:.1%}")
                    else:
                        st.info(f"📊 Average win rate cards — {avg_wr:.1%}")
            else:
                st.info(f"Add {8 - len(deck)} more card(s) to see full analysis.")
