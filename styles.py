import streamlit as st
import os
import streamlit as st
import base64
import os


# ==========================================
# 1. PAGE SETUP & CSS (GLOBAL BACKGROUND)
# ==========================================

def get_base64_image(image_path):
    """Helper to convert image to base64 for CSS embedding"""
    if not os.path.exists(image_path):
        return None
    with open(image_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def setup_page():
    st.set_page_config(page_title="Tactical Cortex", layout="wide", page_icon="🏀")

    # 1. Load the background image
    bin_str = get_base64_image("court.png")

    # 2. Define the CSS
    if bin_str:
        background_css = f"""
            background-image: linear-gradient(rgba(255,255,255,0.85), rgba(255,255,255,0.85)), url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        """
    else:
        background_css = "background-color: #F8F9FB;"

    st.markdown(f"""
    <style>
    /* GLOBAL APP BACKGROUND */
    .stApp {{
        {background_css}
        color: #31333F;
    }}

    /* WAR ROOM OVERLAY */
    .command-overlay {{
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid #E0E0E0;
        border-left: 5px solid #0068C9;
        padding: 30px;
        border-radius: 12px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }}

    /* MAKE DATAFRAMES/TABLES SEMI-TRANSPARENT */
    div[data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.7);
        border-radius: 10px;
        padding: 5px;
    }}

    /* PLAYER CARDS - Container Styling */
    div[data-testid="stVerticalBlock"] > div[style*="border"] {{
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        color: #31333F;
        padding: 10px;
    }}

    /* CAPTION CENTERING */
    div[data-testid="stCaptionContainer"] {{
        text-align: center;
    }}

    /* --- BUTTON STYLES --- */

    /* Standard Button Base */
    div.stButton > button {{
        background-color: #FFFFFF;
        color: #31333F;
        border: 1px solid #D1D5DB;
        transition: all 0.2s;
    }}

    /* Standard Hover (Global) */
    div.stButton > button:not(:disabled):hover {{
        border-color: #FF4B4B;       
        color: #FFFFFF;              
        background-color: #FF4B4B;   
        box-shadow: 0 4px 6px rgba(255, 75, 75, 0.2);
    }}

    /* Primary Button Base (Main Menu) */
    div.stButton > button[kind="primary"] {{
        background-color: #FFFFFF;
        border: 2px solid #0068C9; 
        color: #0068C9;
        font-weight: 800;
        font-size: 20px !important; 
        height: 40px; 
        box-shadow: 0 4px 6px rgba(0, 104, 201, 0.1);
    }}

    /* Primary Hover (Main Menu) */
    div.stButton > button[kind="primary"]:not(:disabled):hover {{
        background-color: #0068C9;
        color: #FFFFFF;
        box-shadow: 0 6px 12px rgba(0, 104, 201, 0.2);
    }}

    /* Disabled State */
    div.stButton > button:disabled {{
        opacity: 0.5;
        cursor: not-allowed;
        background-color: rgba(240, 242, 246, 0.8);
        border-color: #E5E7EB;
        color: #9CA3AF;
        box-shadow: none;
    }}

    /* 👇👇👇 DIALOG BUTTONS (POP-UP) 👇👇👇 */

    /* 1. Equalize Sizes */
    div[role="dialog"] button {{
        min_height: 50px !important;
        height: auto !important;
        width: 100%;
    }}

    /* 2. ACCEPT BUTTON (Green Default) */
    div[role="dialog"] button[kind="primary"] {{
        border-color: #09AB3B !important;
        color: #09AB3B !important;
    }}

    /* 3. ACCEPT BUTTON HOVER (Solid Green) */
    div[role="dialog"] button[kind="primary"]:not(:disabled):hover {{
        background-color: #09AB3B !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 6px rgba(9, 171, 59, 0.2);
    }}

    /* 4. DECLINE BUTTON (Red Default) */
    div[role="dialog"] button:not([kind="primary"]) {{
        border-color: #FF4B4B !important;
        color: #FF4B4B !important;
    }}

    /* 5. 👇 DECLINE BUTTON HOVER (Fixes Invisible Text) 👇 */
    div[role="dialog"] button:not([kind="primary"]):not(:disabled):hover {{
        background-color: #FF4B4B !important;
        color: #FFFFFF !important; /* Forces Text to White */
        border-color: #FF4B4B !important;
    }}

    /* --- DIALOG LOCK (INVISIBLE SHIELD) --- */
    div[role="dialog"] {{
        overflow: visible !important;
    }}
    div[role="dialog"]::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: transparent;
        z-index: -1;
    }}
    div[role="dialog"] button[aria-label="Close"] {{
        display: none !important;
    }}


    </style>
    """, unsafe_allow_html=True)
#
# ==========================================
# 2. COMPONENT: PLAYER CARDS (ON COURT)
# ==========================================
def render_court_view(active_names, live_stats_df, roster_df):
    """
    Renders the top 'Court' section with 5 player cards.
    Now includes LARGER PTS, REB, AST, STL, BLK, PF.
    """

    # 👇 CHANGED: Replaced standard markdown with HTML to reduce gap
    st.markdown("""
    <h3 style='margin-top: -20px; margin-bottom: 15px;'>
        ⚡ ON COURT: ACTIVE ROTATION
    </h3>
    """, unsafe_allow_html=True)

    cols = st.columns(5)

    for i, p_name in enumerate(active_names):
        # 1. Data Extraction
        stats = live_stats_df.loc[p_name]

        p_row = roster_df[roster_df['Player'] == p_name].iloc[0]
        raw_pos = p_row.get('Positions', p_row.get('Position', []))
        pos = raw_pos[0] if len(raw_pos) > 0 else "N/A"

        # Extract stats
        pts = int(stats['PTS'])
        reb = int(stats['TRB'])
        ast = int(stats['AST'])
        stl = int(stats['STL'])
        blk = int(stats['BLK'])
        pf = int(stats['PF'])
        mins = int(stats['MIN'])

        # Color Logic for Fouls
        pf_color = "#FF4B4B" if pf >= 4 else "#31333F"

        # Styles
        box_style = "text-align: center; width: 33%;"
        label_style = "font-size: 13px; color: #888; font-weight: 700; letter-spacing: 0.5px; margin-bottom: 2px;"
        val_style = "font-size: 24px; color: #0068C9; font-weight: 800; line-height: 1.1;"
        pf_val_style = f"font-size: 24px; color: {pf_color}; font-weight: 800; line-height: 1.1;"
        border_style = "border-right: 1px solid #eee;"

        with cols[i]:
            with st.container(border=True):
                # --- NEW IMAGE LOGIC START ---
                img_path = f"player_imgs/{p_name}.png"

                # Check if local image exists, otherwise use placeholder
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True)
                else:
                    st.image(f"https://placehold.co/150x150/F8F9FB/0068C9/png?text={p_name.split()[-1]}",
                             use_container_width=True)
                # --- NEW IMAGE LOGIC END ---

                # B. Name & Position
                st.markdown(
                    f"<div style='text-align: center; font-weight: bold; margin-top: 8px; font-size: 20px;'>{p_name}</div>",
                    unsafe_allow_html=True)
                st.markdown(
                    f"<div style='text-align: center; color: #888; font-size: 22px; margin-bottom: 12px;'>{pos}</div>",
                    unsafe_allow_html=True)

                # C. 6-Stat Grid (HTML)
                st.markdown(f"""
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #f0f0f0; padding-bottom: 8px;">
                        <div style="{box_style} {border_style}"><div style="{label_style}">PTS</div><div style="{val_style}">{pts}</div></div>
                        <div style="{box_style} {border_style}"><div style="{label_style}">REB</div><div style="{val_style}">{reb}</div></div>
                        <div style="{box_style}"><div style="{label_style}">AST</div><div style="{val_style}">{ast}</div></div>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <div style="{box_style} {border_style}"><div style="{label_style}">STL</div><div style="{val_style}">{stl}</div></div>
                        <div style="{box_style} {border_style}"><div style="{label_style}">BLK</div><div style="{val_style}">{blk}</div></div>
                        <div style="{box_style}"><div style="{label_style}">PF</div><div style="{pf_val_style}">{pf}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # D. Minutes Footer
                st.caption(f"⏱️ MIN: {mins}")

    st.divider()    # ==========================================
# 3. COMPONENT: WAR ROOM (OVERLAY)
# ==========================================
def render_war_room_header():
    """Starts the HTML div for the War Room style"""
    st.markdown("<div class='command-overlay'>", unsafe_allow_html=True)
    st.subheader("🧠 ECOACH WAR ROOM") # Renamed


def render_war_room_footer():
    """Closes the HTML div"""
    st.markdown("</div>", unsafe_allow_html=True)


def render_gap_vector(gap_vector):
    """Displays the stats impact grid inside the War Room"""
    if gap_vector:
        st.markdown("**PROJECTED SEASONAL IMPACT (Avg/Game Delta):**")
        cols = st.columns(len(gap_vector))
        for i, (stat, val) in enumerate(gap_vector.items()):
            cols[i].metric(stat, val)


# ==========================================
# 4. COMPONENT: BENCH TABLE
# ==========================================
def render_bench_table(live_stats_df, active_names):
    """
    Renders the styled dataframe for the bench.
    """
    st.subheader("🪑 BENCH PERFORMANCE")

    # Filter: Only show players NOT in active lineup
    bench_mask = ~live_stats_df.index.isin(active_names)
    bench_df = live_stats_df[bench_mask].round(0).astype(int)

    # Columns to display
    cols_to_show = ['MIN', 'PTS', 'TRB', 'AST', 'STL', 'BLK', 'PF']

    # Apply 'Blues' gradient (Light mode friendly)
    styled_df = bench_df[cols_to_show].style.background_gradient(cmap="Blues", subset=['PTS', 'TRB'])

    st.dataframe(styled_df, use_container_width=True, height=300)


# ==========================================
# 5. OFFLINE SCREEN
# ==========================================
def render_offline_screen():
    # CHANGED: Branding to Ecoach
    st.title("🏀 WELCOME TO ECOACH PROJECT")
    st.markdown("### INSTRUCTIONS:")
    st.info("1. Enter User Name in Sidebar\n2. Select Team\n3. Click **Initiate Session**")