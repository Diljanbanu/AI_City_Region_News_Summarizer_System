"""
🏙️ AI-Powered City & Region News Summarization System
IP-based location detection with strict city filtering, live news feeds,
and Google Gemini AI summarization.
"""

import json
import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

from api_services.location_service import (
    get_location_by_ip,
    format_location_info,
    get_location_hierarchy,
    normalize_city_name,
)
from api_services.weather_service import get_live_weather
from api_services.news_service import (
    fetch_live_news,
    scrape_full_article_content,
    CATEGORIES,
)
from api_services.ai_summary_service import generate_ai_news_summary

load_dotenv()

st.set_page_config(
    page_title="City & Region News AI",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── State → City Mapping for Manual Selection ──────────────────────────────
STATE_CITY_MAP = {
    "🌿 Gujarat": [
        "Rajkot", "Gadhka (Rajkot)", "Ahmedabad", "Surat", "Vadodara",
        "Jamnagar", "Gandhinagar", "Junagadh", "Bhavnagar", "Morbi",
        "Anand", "Navsari", "Nadiad", "Surendranagar", "Bharuch", "Vapi",
    ],
    "🏙️ Maharashtra": [
        "Mumbai", "Pune", "Nagpur", "Nashik", "Thane",
        "Chhatrapati Sambhajinagar", "Solapur", "Amravati", "Kolhapur",
    ],
    "🏰 Delhi (UT)": ["New Delhi", "North Delhi", "South Delhi", "East Delhi", "West Delhi"],
    "🌴 Karnataka": ["Bengaluru", "Mysuru", "Mangaluru", "Hubballi-Dharwad", "Belagavi", "Shivamogga"],
    "🏰 Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer", "Bikaner"],
    "🌊 Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    "🏛️ Uttar Pradesh": ["Lucknow", "Kanpur", "Varanasi", "Agra", "Noida", "Ghaziabad", "Prayagraj"],
    "🌉 West Bengal": ["Kolkata", "Howrah", "Durgapur", "Siliguri", "Asansol"],
    "🌴 Kerala": ["Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur"],
    "🚩 Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
    "🗽 New York (USA)": ["New York City", "Buffalo", "Rochester", "Albany"],
    "🏰 London / England (UK)": ["London", "Manchester", "Birmingham", "Leeds", "Liverpool"],
}

# ─── Styling ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background: #04070F;
}

/* ── Hero Banner ── */
.hero {
    background: linear-gradient(135deg, #04070F 0%, #0A1628 45%, #0D2B5E 100%);
    padding: 2.2rem 2.5rem 1.8rem;
    border-radius: 20px;
    border: 1px solid rgba(59,130,246,0.25);
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::after {
    content: "";
    position: absolute;
    right: -60px; top: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(59,130,246,0.18) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-size: 2.3rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    background: linear-gradient(100deg, #FFFFFF 0%, #60A5FA 55%, #A78BFA 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.3rem;
}
.hero-sub {
    color: #94A3B8;
    font-size: 0.98rem;
    font-weight: 500;
}

/* ── Location Card ── */
.loc-card {
    background: linear-gradient(145deg, #0B1120, #111827);
    border: 1px solid rgba(255,255,255,0.07);
    border-top: 3px solid;
    border-radius: 14px;
    padding: 0.9rem 1.1rem;
    height: 100%;
}
.loc-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748B; font-weight: 700; margin-bottom: 0.3rem; }
.loc-value { font-size: 1.15rem; font-weight: 800; color: #F1F5F9; line-height: 1.2; }
.loc-sub   { font-size: 0.78rem; color: #475569; margin-top: 0.2rem; font-weight: 500; }

/* ── Filter Status Alert ── */
.filter-banner {
    background: linear-gradient(90deg, rgba(34,197,94,0.12) 0%, rgba(59,130,246,0.12) 100%);
    border: 1px solid rgba(34,197,94,0.35);
    border-radius: 12px;
    padding: 0.75rem 1.2rem;
    color: #4ADE80;
    font-size: 0.92rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 1rem 0;
}

/* ── News Card ── */
.ncard {
    background: linear-gradient(145deg, #0B1120, #0F172A);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1rem;
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}
.ncard:hover {
    border-color: rgba(59,130,246,0.45);
    box-shadow: 0 12px 32px -8px rgba(59,130,246,0.18);
}
.ncard-engine {
    display: inline-block;
    background: rgba(34,197,94,0.15);
    color: #4ADE80;
    border: 1px solid rgba(74,222,128,0.3);
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.2rem 0.6rem;
    margin-bottom: 0.6rem;
}
.ncard-source {
    font-size: 0.8rem;
    color: #38BDF8;
    font-weight: 600;
    margin-bottom: 0.4rem;
}
.ncard-title {
    font-size: 1.08rem;
    font-weight: 800;
    color: #F1F5F9;
    line-height: 1.4;
    margin-bottom: 0.7rem;
}
.ncard-snippet {
    font-size: 0.88rem;
    color: #94A3B8;
    line-height: 1.55;
    margin-bottom: 0.8rem;
}
.ncard-date { font-size: 0.78rem; color: #475569; font-weight: 500; }

/* ── AI Summary Box ── */
.ai-box {
    background: linear-gradient(145deg, #04070F 0%, #160A2E 60%, #0B1120 100%);
    border: 1px solid #7C3AED;
    border-radius: 20px;
    padding: 2rem;
    box-shadow: 0 20px 50px -15px rgba(124,58,237,0.35);
}
.ai-headline {
    font-size: 1.25rem;
    font-weight: 900;
    color: #EDE9FE;
    margin-bottom: 0.5rem;
}
.ai-meta { font-size: 0.82rem; color: #A78BFA; font-weight: 600; margin-bottom: 1.2rem; }
.section-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #60A5FA;
    font-weight: 800;
    margin-top: 1.2rem;
    margin-bottom: 0.5rem;
}
.ai-summary-text {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-size: 1rem;
    line-height: 1.65;
    color: #E2E8F0;
}
.ai-main-event {
    background: rgba(59,130,246,0.1);
    border-left: 4px solid #3B82F6;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    font-size: 0.97rem;
    color: #BFDBFE;
    font-weight: 600;
    line-height: 1.5;
}
.kp {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    background: rgba(255,255,255,0.03);
    border-left: 3px solid #60A5FA;
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    margin-bottom: 0.45rem;
    font-size: 0.92rem;
    color: #CBD5E1;
    line-height: 1.45;
}
.ai-impact {
    background: rgba(124,58,237,0.1);
    border-left: 4px solid #7C3AED;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    font-size: 0.95rem;
    color: #DDD6FE;
    line-height: 1.6;
}
.badge {
    display: inline-block;
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.22rem 0.65rem;
    margin-right: 0.35rem;
}
.b-blue   { background:rgba(59,130,246,0.18); color:#60A5FA; border:1px solid rgba(96,165,250,0.3); }
.b-violet { background:rgba(124,58,237,0.18); color:#A78BFA; border:1px solid rgba(167,139,250,0.3); }
.b-amber  { background:rgba(245,158,11,0.18); color:#FCD34D; border:1px solid rgba(252,211,77,0.3); }
.b-green  { background:rgba(34,197,94,0.18);  color:#4ADE80; border:1px solid rgba(74,222,128,0.3); }

/* ── Category Navigation Bar ── */
.category-nav-card {
    background: linear-gradient(135deg, rgba(11, 17, 32, 0.95) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(59, 130, 246, 0.28);
    border-radius: 16px;
    padding: 0.9rem 1.25rem 0.6rem;
    margin-top: -0.5rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.6), 0 0 24px rgba(59, 130, 246, 0.12);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    animation: fadeInCategoryNav 0.4s ease-out;
}
.category-nav-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.07);
}
.category-nav-label {
    font-size: 0.82rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94A3B8;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.category-active-chip {
    font-size: 0.78rem;
    font-weight: 700;
    color: #60A5FA;
    background: rgba(59, 130, 246, 0.16);
    border: 1px solid rgba(96, 165, 250, 0.35);
    border-radius: 99px;
    padding: 0.18rem 0.75rem;
}

/* Category Pills & Interactive Elements */
div[data-testid="stPills"], div[data-testid="stButtonGroup"] {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 0.55rem !important;
    width: 100% !important;
    align-items: center !important;
}

div[data-testid="stPills"] button, div[data-testid="stButtonGroup"] button {
    border-radius: 999px !important;
    padding: 0.48rem 1.2rem !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.015em !important;
    color: #94A3B8 !important;
    background: rgba(15, 23, 42, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2) !important;
    transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
}

div[data-testid="stPills"] button:hover, div[data-testid="stButtonGroup"] button:hover {
    color: #FFFFFF !important;
    border-color: rgba(96, 165, 250, 0.5) !important;
    background: rgba(30, 41, 59, 0.95) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(59, 130, 246, 0.25) !important;
}

/* Active Category Pill Indicator */
div[data-testid="stPills"] button[aria-checked="true"],
div[data-testid="stPills"] button[aria-selected="true"],
div[data-testid="stPills"] button[data-selected="true"],
div[data-testid="stButtonGroup"] button[aria-checked="true"],
div[data-testid="stButtonGroup"] button[aria-selected="true"] {
    background: linear-gradient(135deg, #2563EB 0%, #7C3AED 100%) !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    border: 1px solid rgba(196, 181, 253, 0.65) !important;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.6), 0 4px 14px rgba(0, 0, 0, 0.35) !important;
    transform: scale(1.04) !important;
}

/* ── Smooth Animations ── */
@keyframes fadeInCategoryNav {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInUpNews {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.ncard {
    animation: fadeInUpNews 0.42s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* Priority Badges */
.prio-p1 {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(16, 185, 129, 0.18);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.45);
    border-radius: 99px;
    font-size: 0.74rem;
    font-weight: 800;
    padding: 0.22rem 0.7rem;
    margin-right: 0.35rem;
    box-shadow: 0 0 12px rgba(16, 185, 129, 0.25);
}

.prio-p2 {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(59, 130, 246, 0.18);
    color: #60A5FA;
    border: 1px solid rgba(96, 165, 250, 0.45);
    border-radius: 99px;
    font-size: 0.74rem;
    font-weight: 800;
    padding: 0.22rem 0.7rem;
    margin-right: 0.35rem;
}

.cat-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: rgba(168, 85, 247, 0.18);
    color: #C084FC;
    border: 1px solid rgba(192, 132, 252, 0.4);
    border-radius: 99px;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.22rem 0.65rem;
    margin-right: 0.35rem;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Initialization ───────────────────────────────────────────
for key in ("raw_loc", "selected_article", "ai_summary", "last_queried_target", "selected_category"):
    if key not in st.session_state:
        st.session_state[key] = "🌐 All" if key == "selected_category" else None

# ─── Sidebar – API Key Settings ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ API Configuration")
    gemini_key   = st.text_input("🤖 GEMINI_API_KEY",  value=os.getenv("GEMINI_API_KEY",  ""), type="password")
    ipinfo_token = st.text_input("📍 IPINFO_TOKEN",     value=os.getenv("IPINFO_TOKEN",    ""), type="password")
    news_key     = st.text_input("📰 NEWS_API_KEY",     value=os.getenv("NEWS_API_KEY",    ""), type="password")
    gnews_key    = st.text_input("📰 GNEWS_API_KEY",    value=os.getenv("GNEWS_API_KEY",   ""), type="password")
    st.divider()
    if st.button("🔄 Re-detect IP & Reset All", use_container_width=True):
        st.session_state.raw_loc = None
        st.session_state.selected_article = None
        st.session_state.ai_summary = None
        st.session_state.last_queried_target = None
        st.rerun()

# ─── Hero Banner (Main Navigation Bar) ─────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">🏙️ AI City & Region News Summarizer</div>
  <div class="hero-sub">Automatic IP Geolocation • City-Filtered Live News • Google Gemini AI Summarization</div>
</div>
""", unsafe_allow_html=True)

# ─── 1 · News Category Navigation Bar ──────────────────────────────────────
# Horizontal navigation bar positioned directly below the main navigation bar
CATEGORY_NAV_ITEMS = [
    "🌐 All",
    "🏛️ Political",
    "⚽ Sports",
    "💻 Technology",
    "📈 Business",
    "🎬 Entertainment",
    "🎓 Education",
    "📍 Local News",
]

current_cat = st.session_state.selected_category or "🌐 All"

st.markdown(f"""
<div class="category-nav-card">
  <div class="category-nav-header">
    <div class="category-nav-label">
      <span>📑 NEWS CATEGORIES</span>
      <span style="font-size:0.72rem;color:#64748B;font-weight:500;">• Instant sector & hyperlocal filtering</span>
    </div>
    <div class="category-active-chip">Active: {current_cat}</div>
  </div>
</div>
""", unsafe_allow_html=True)

chosen_cat = st.pills(
    label="News Category Navigation Bar",
    options=CATEGORY_NAV_ITEMS,
    default=current_cat,
    selection_mode="single",
    label_visibility="collapsed",
    key="horizontal_category_nav_pills",
)

if chosen_cat and chosen_cat != st.session_state.selected_category:
    st.session_state.selected_category = chosen_cat
    st.session_state.selected_article = None
    st.session_state.ai_summary = None
    st.rerun()

# ─── 2 · Auto-Detect IP Location ───────────────────────────────────────────
if st.session_state.raw_loc is None:
    with st.spinner("📍 Detecting location from your IP address via ipinfo.io..."):
        st.session_state.raw_loc = get_location_by_ip(ipinfo_token=ipinfo_token)

raw_loc   = st.session_state.raw_loc
auto_city = raw_loc.get("city", "Rajkot")
auto_region = raw_loc.get("region", "Gujarat")
auto_country = raw_loc.get("country", "India")
auto_ip   = raw_loc.get("ip", "Auto-detected")

# ─── 3 · Dynamic Location Selector ──────────────────────────────────────────
st.markdown("### 🗺️ Location & News Filter Controls")

mode_options = [
    f"📍 My IP Location: {auto_city} (City News)",
    f"🌎 My IP Region: {auto_region} (Regional News)",
    "🏙️ Select Another City (Dropdown)",
    "✍️ Enter Custom City / Village / Region",
]

col_mode, col_extra = st.columns([2.5, 3.5])

with col_mode:
    selected_mode = st.radio(
        "Choose Search Target:",
        options=mode_options,
        index=0,
        key="location_mode_radio",
    )

with col_extra:
    if "Select Another City" in selected_mode:
        sc1, sc2 = st.columns(2)
        with sc1:
            state_list = list(STATE_CITY_MAP.keys())
            match_idx = next((i for i, s in enumerate(state_list) if auto_region.lower() in s.lower()), 0)
            chosen_state = st.selectbox("Select State:", state_list, index=match_idx, key="manual_state")
        with sc2:
            city_list = STATE_CITY_MAP.get(chosen_state, ["Rajkot"])
            city_idx = 0
            for i, c in enumerate(city_list):
                if auto_city.lower() in c.lower():
                    city_idx = i
                    break
            chosen_city = st.selectbox(f"Select City in {chosen_state.split(' ',1)[-1]}:", city_list, index=city_idx, key="manual_city")
        
        target_city = chosen_city.split("(", 1)[0].strip() if "(" in chosen_city else chosen_city
        emoji_strip = str.maketrans("", "", "🌿🏙️🏰🌴🌊🏛️🌉🚩🗽📍✍️ ")
        target_state = chosen_state.translate(emoji_strip).strip()
        search_type = "city"

    elif "Enter Custom" in selected_mode:
        custom_input = st.text_input("Type city, village, or region name (e.g. Gadhka):", value=auto_city, key="custom_city_box")
        target_city = custom_input.strip() or auto_city
        target_state = auto_region
        search_type = "city"

    elif "Regional News" in selected_mode:
        target_city = auto_city
        target_state = auto_region
        search_type = "region"
        st.info(f"Showing regional news across the state of **{auto_region}**.")

    else:
        # Default: 📍 My IP Location (City News)
        target_city = auto_city
        target_state = auto_region
        search_type = "city"
        st.success(f"✅ Filter Active: Automatically searching live news strictly for **{auto_city}**, {auto_region} based on your IP.")

target_query = target_city if search_type == "city" else target_state

# Location hierarchy context for accurate prioritization
hierarchy = get_location_hierarchy(target_query, target_state)

# Clear stale AI summary if target location or category changed
cache_key = f"{target_query}_{st.session_state.selected_category}_{search_type}"
if st.session_state.last_queried_target != cache_key:
    st.session_state.selected_article = None
    st.session_state.ai_summary = None
    st.session_state.last_queried_target = cache_key

# Weather context
weather = get_live_weather(raw_loc.get("lat", 22.30), raw_loc.get("lon", 70.80), target_city)

# ─── 4 · Location & Status KPI Cards ────────────────────────────────────────
kpi = st.columns(6)
cards = [
    ("🏙️ Detected City",     auto_city,          "#3B82F6"),
    ("🌎 State / Region",    auto_region,        "#8B5CF6"),
    ("🎯 Active Filter",     target_query,       "#F59E0B"),
    ("📑 Category",          st.session_state.selected_category, "#8B5CF6"),
    ("🌤️ Weather",           f"{weather['temperature']} {weather['condition']}", "#10B981"),
    ("📡 Public IP",         auto_ip,            "#64748B"),
]
for col, (label, value, color) in zip(kpi, cards):
    col.markdown(f"""
    <div class="loc-card" style="border-top-color:{color}">
        <div class="loc-label">{label}</div>
        <div class="loc-value">{value}</div>
    </div>""", unsafe_allow_html=True)

# ─── Strict Filter & Location Prioritization Confirmation Banner ───────────
if st.session_state.selected_category == "📍 Local News":
    st.markdown(f"""
    <div class="filter-banner" style="border-color:rgba(16,185,129,0.4);background:linear-gradient(90deg,rgba(16,185,129,0.15) 0%,rgba(59,130,246,0.12) 100%);">
      <span>🎯</span>
      <span><strong>LOCAL NEWS PRIORITIZATION ACTIVE:</strong> Prioritizing news for <u>{hierarchy['primary']}</u> & nearby areas (Priority 1), followed by <u>{hierarchy['district']}</u> (Priority 2). Distant unrelated locations (e.g. Bhavnagar) are strictly filtered out.</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="filter-banner">
      <span>🛡️</span>
      <span><strong>CATEGORY & LOCATION FILTER ACTIVE:</strong> Displaying verified <strong>{st.session_state.selected_category}</strong> news reporting on <u>{target_query}</u> ({target_state}). Unrelated stories are filtered out.</span>
    </div>
    """, unsafe_allow_html=True)

# ─── 5 · Fetch & Display Filtered Live News ─────────────────────────────────
category_heading = "All Categories" if st.session_state.selected_category == "🌐 All" else st.session_state.selected_category
st.markdown(f"### 📰 Latest {category_heading} News for **{target_query}** ({target_state})")

with st.spinner(f"Fetching live {category_heading.lower()} news matching '{target_query}'..."):
    articles = fetch_live_news(
        query_location=target_query,
        search_type=search_type,
        region_state=target_state,
        category=st.session_state.selected_category,
        news_api_key=news_key,
        gnews_api_key=gnews_key,
        limit=6,
    )

if not articles:
    st.warning(f"No recent {category_heading.lower()} news found specifically mentioning '{target_query}'.")
else:
    cols = st.columns(2)
    for i, art in enumerate(articles):
        with cols[i % 2]:
            prio_badge_html = ""
            if art.get("location_priority"):
                prio_txt = art["location_priority"]
                if "Priority 1" in prio_txt:
                    prio_badge_html = f'<span class="prio-p1">🎯 {prio_txt}</span>'
                else:
                    prio_badge_html = f'<span class="prio-p2">🏙️ {prio_txt}</span>'

            cat_badge_html = f'<span class="cat-badge">{art.get("category_badge", "📰 News")}</span>'

            st.markdown(f"""
            <div class="ncard">
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;flex-wrap:wrap;gap:0.4rem;">
                <div class="ncard-engine">{art.get('api_engine','Verified News')}</div>
                <div>{cat_badge_html} {prio_badge_html}</div>
              </div>
              <div class="ncard-source">📰 {art['source']} &nbsp;•&nbsp; <span class="ncard-date">{art['published_at']}</span></div>
              <div class="ncard-title">{art['title']}</div>
              <div class="ncard-snippet">{art['summary_preview']}</div>
              <div style="margin-top:0.6rem;">
                <span class="badge b-blue">📍 {art.get('location', target_query)}</span>
                <span class="badge b-violet">🌎 {target_state}</span>
                <span class="badge b-green">✅ Verified Match</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            b1, b2 = st.columns([3, 2])
            with b1:
                if st.button("🤖 Summarize with AI", key=f"ai_{art['id']}_{i}", type="primary", use_container_width=True):
                    art["location"] = target_query
                    art["full_text"] = scrape_full_article_content(art["link"], art.get("full_text",""))
                    with st.spinner(f"🤖 Gemini AI is analyzing the article for {target_query}..."):
                        st.session_state.selected_article = art
                        st.session_state.ai_summary = generate_ai_news_summary(art, gemini_api_key=gemini_key)
                    st.rerun()
            with b2:
                st.markdown(
                    f"<a href='{art['link']}' target='_blank'>"
                    f"<button style='width:100%;padding:0.46rem 0;border-radius:10px;"
                    f"border:1px solid #334155;background:#1E293B;color:#CBD5E1;"
                    f"font-weight:600;font-size:0.85rem;cursor:pointer;'>🔗 Read Full</button></a>",
                    unsafe_allow_html=True,
                )
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# ─── 5 · AI Summary Output ──────────────────────────────────────────────────
if st.session_state.selected_article and st.session_state.ai_summary:
    sel = st.session_state.selected_article
    sm  = st.session_state.ai_summary

    st.markdown("---")
    st.markdown("### 🤖 AI-Generated News Summary")

    st.markdown(f"""
    <div class="ai-box">
      <div style="display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap;margin-bottom:0.5rem;">
        <span class="badge b-violet">{sm.get('ai_engine','Gemini AI 🤖')}</span>
        <span class="badge b-amber">Category: {sm.get('category','News 📰')}</span>
        <span class="badge" style="background:rgba(239,68,68,0.18);color:#FCA5A5;border:1px solid rgba(252,165,165,0.3);">
          Urgency: {sm.get('urgency_level','Medium')}
        </span>
        <span class="badge b-blue">Location: {target_query}, {target_state}</span>
      </div>
      <div class="ai-headline">📌 {sel['title']}</div>
      <div class="ai-meta">
        Source: {sel['source']} &nbsp;|&nbsp;
        Published: {sel['published_at']} &nbsp;|&nbsp;
        Target Location: {target_query}, {target_state}
      </div>

      <div class="section-label">📝 Concise Summary</div>
      <div class="ai-summary-text">{sm.get('concise_summary','')}</div>

      <div class="section-label">🎯 Main Event</div>
      <div class="ai-main-event">{sm.get('main_event','')}</div>

      <div class="section-label">🔑 Key Highlights</div>
    """, unsafe_allow_html=True)

    for pt in sm.get("important_points", []):
        st.markdown(f"<div class='kp'>▸ {pt}</div>", unsafe_allow_html=True)

    st.markdown(f"""
      <div class="section-label">🏙️ Impact on {target_query}, {target_state}</div>
      <div class="ai-impact">{sm.get('regional_impact','')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("📋 Show Raw JSON Output", use_container_width=False):
        st.code(json.dumps(sm, indent=2), language="json")

# ─── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#475569;font-size:0.82rem;padding:0.8rem 0'>"
    "🏙️ AI-Powered City / Region News Summarizer &nbsp;•&nbsp; "
    "Python · Streamlit · Google Gemini AI · IPInfo.io · Open-Meteo"
    "</div>",
    unsafe_allow_html=True,
)
