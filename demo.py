import streamlit as st
import pandas as pd
import numpy as np
import styles  # Importing the provided styles.py

# ==========================================
# 0. MOCK DATA & CONFIG
# ==========================================
ROSTER_DATA = {
    "Player": [
        "LeBron James", "Anthony Davis", "Austin Reaves", "Rui Hachimura", "D'Angelo Russell",
        "Jarred Vanderbilt", "Gabe Vincent", "Taurean Prince", "Jaxson Hayes", "Max Christie", "Christian Wood"
    ],
    "Positions": [
        ["SF"], ["C"], ["SG"], ["PF"], ["PG"],
        ["PF"], ["PG"], ["SF"], ["C"], ["SG"], ["C"]
    ]
}

INITIAL_STARTERS = ["D'Angelo Russell", "Austin Reaves", "LeBron James", "Rui Hachimura", "Anthony Davis"]

# Random "System Thoughts" for minutes 1-9
SYSTEM_NOTES = [
    "✅ Spacing optimal. No changes needed.",
    "✅ Defensive rating stable at 104.2.",
    "✅ Pace is high (102.5). Starters managing fatigue well.",
    "✅ Matchups favorable. Hold current rotation.",
    "✅ Offensive flow efficient. Rebounding rate +5%."
]


def get_initial_stats(roster_df):
    df = pd.DataFrame(index=roster_df["Player"])
    cols = ['MIN', 'PTS', 'TRB', 'AST', 'STL', 'BLK', 'PF']
    for c in cols: df[c] = 0
    return df


def simulate_minute(stats_df, active_players):
    for player in active_players:
        stats_df.loc[player, 'MIN'] += 1
        if np.random.rand() > 0.6: stats_df.loc[player, 'PTS'] += np.random.choice([2, 3])
        if np.random.rand() > 0.8: stats_df.loc[player, 'TRB'] += 1
        if np.random.rand() > 0.85: stats_df.loc[player, 'AST'] += 1
        if np.random.rand() > 0.95: stats_df.loc[player, 'PF'] += 1
    return stats_df


# ==========================================
# 1. APP LOGIC
# ==========================================
styles.setup_page()

if 'game_active' not in st.session_state:
    st.session_state['game_active'] = False
if 'roster' not in st.session_state:
    st.session_state['roster'] = pd.DataFrame(ROSTER_DATA)
if 'active_lineup' not in st.session_state:
    st.session_state['active_lineup'] = INITIAL_STARTERS
if 'stats' not in st.session_state:
    st.session_state['stats'] = get_initial_stats(st.session_state['roster'])
if 'game_time' not in st.session_state:
    st.session_state['game_time'] = 0
if 'suggestion_approved' not in st.session_state:
    st.session_state['suggestion_approved'] = False

# ==========================================
# 2. VIEW: START SCREEN
# ==========================================
if not st.session_state['game_active']:
    styles.render_offline_screen()
    with st.sidebar:
        st.header("⚙️ Setup")
        api_key = st.text_input("Enter OpenAI API Key", type="password")
        team = st.selectbox("Select Team", ["Los Angeles Lakers", "Golden State Warriors", "Boston Celtics"])
        st.markdown("---")
        if st.button("Initiate Session", type="primary", use_container_width=True):
            if api_key:
                st.session_state['game_active'] = True
                st.rerun()
            else:
                st.warning("⚠️ Enter dummy key to start.")

# ==========================================
# 3. VIEW: LIVE GAME DASHBOARD
# ==========================================
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.header("🎮 Game Control")
        st.metric("Game Time", f"{st.session_state['game_time']}:00")
        st.markdown("---")
        if st.button("⏱️ +1 MINUTE", use_container_width=True):
            st.session_state['game_time'] += 1
            st.session_state['stats'] = simulate_minute(st.session_state['stats'], st.session_state['active_lineup'])
            st.rerun()
        st.markdown("---")
        if st.button("🛑 END GAME", use_container_width=True):
            st.session_state['game_active'] = False
            st.session_state['game_time'] = 0
            st.session_state['stats'] = get_initial_stats(st.session_state['roster'])
            st.rerun()

    # --- HEADER ---
    c1, c2, c3 = st.columns([1, 6, 1])
    with c2:
        st.markdown(f"<h2 style='text-align: center;'>🏀 ECOACH LIVE | {st.session_state['game_time']}:00 | Q1</h2>",
                    unsafe_allow_html=True)

    # --- TOP: PLAYERS ---
    styles.render_court_view(st.session_state['active_lineup'], st.session_state['stats'], st.session_state['roster'])

    # --- MIDDLE: SYSTEM BRAIN ---
    # Centered container for system messages
    brain_col1, brain_col2, brain_col3 = st.columns([1, 8, 1])

    with brain_col2:
        # SCENARIO 1: PRE-GAME
        if st.session_state['game_time'] == 0:
            st.info("ℹ️ **SYSTEM READY:** Waiting for tip-off to begin analysis...")

        # SCENARIO 2: MINUTES 1-9 (MONITORING)
        elif 0 < st.session_state['game_time'] < 10:
            # Pick a random note based on time to make it feel alive
            note_idx = st.session_state['game_time'] % len(SYSTEM_NOTES)
            active_note = SYSTEM_NOTES[note_idx]

            with st.container(border=True):
                st.markdown(f"""
                <div style="text-align: center; padding: 10px;">
                    <h4 style="margin:0; color: #0068C9;">⚡ SYSTEM ACTIVE: MONITORING ROTATION</h4>
                    <p style="margin-top: 10px; font-size: 16px;">{active_note}</p>
                    <p style="color: grey; font-size: 12px;"><i>Analyzing real-time telemetry... No substitutions suggested.</i></p>
                </div>
                """, unsafe_allow_html=True)

        # SCENARIO 3: MINUTE 10+ (WAR ROOM TRIGGER)
        elif st.session_state['game_time'] >= 10 and not st.session_state['suggestion_approved']:
            styles.render_war_room_header()
            st.markdown("#### 🚨 ROTATION ALERT")

            c_wr1, c_wr2, c_wr3 = st.columns([1, 2, 1])
            sub_in, sub_out = "Jarred Vanderbilt", "Rui Hachimura"

            with c_wr1:
                st.info(f"**SUB OUT**\n\n📉 {sub_out}")
            with c_wr2:
                st.markdown(
                    f"**Reasoning:** {sub_out} is showing defensive fatigue.\n\n**Proposal:** Bring in **{sub_in}** for speed match.")
                styles.render_gap_vector({"DEF Rating": "+4.2", "Pace": "+2.1"})
            with c_wr3:
                st.success(f"**SUB IN**\n\n📈 {sub_in}")

            b1, b2 = st.columns([1, 4])
            with b1:
                if st.button("✅ APPROVE", type="primary"):
                    st.session_state['active_lineup'][st.session_state['active_lineup'].index(sub_out)] = sub_in
                    st.session_state['suggestion_approved'] = True
                    st.rerun()
            with b2:
                if st.button("❌ DECLINE"):
                    st.session_state['suggestion_approved'] = True
                    st.rerun()
            styles.render_war_room_footer()

        # SCENARIO 4: SUB APPROVED (BACK TO MONITORING)
        elif st.session_state['suggestion_approved']:
            with st.container(border=True):
                st.markdown("""
                <div style="text-align: center; color: green; padding: 10px;">
                    <h4 style="margin:0;">✅ ROTATION ADJUSTED</h4>
                    <p>New lineup calibration complete. Resuming monitoring.</p>
                </div>
                """, unsafe_allow_html=True)

    # --- BOTTOM: BENCH ---
    st.markdown("<br>", unsafe_allow_html=True)  # Spacer
    styles.render_bench_table(st.session_state['stats'], st.session_state['active_lineup'])