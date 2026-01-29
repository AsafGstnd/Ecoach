# import streamlit as st
# import pandas as pd
# import numpy as np
# import traceback
# import time
# import os
# # Custom Modules
# import solver
# from translator import TacticalTranslator
# import styles
#
#
# # ==========================================
# # 1. DATA & LOGIC ENGINE
# # ==========================================
# @st.cache_data
# def load_and_clean_data(filepath):
#     try:
#         df = pd.read_csv(filepath)
#         df.columns = [c.strip().replace('▲', '') for c in df.columns]
#
#         col_map = {'Avg minutes played': 'Avg minutes p'}
#         df = df.rename(columns=col_map)
#
#         # Convert Positions column to list format
#         def normalize_positions(pos):
#             if pd.isnull(pos):
#                 return []
#             if isinstance(pos, list):
#                 return [str(p).strip() for p in pos if pd.notnull(p)]
#             # If it's a string, split by comma if multiple positions
#             pos_str = str(pos).strip()
#             if ',' in pos_str:
#                 return [p.strip() for p in pos_str.split(',') if p.strip()]
#             return [pos_str] if pos_str else []
#
#         df['Position'] = df['Position'].apply(normalize_positions)
#
#         # Ensure numeric columns are actually numeric
#         target_cols = ['PTS', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'Avg minutes p', 'ORB', 'DRB', 'TRB', '3P%', '2P%',
#                        'eFG%', 'FT%']
#         for col in target_cols:
#             if col in df.columns:
#                 df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
#             else:
#                 df[col] = 0.0
#         return df
#     except Exception as e:
#         st.error(f"Data Error: {e}")
#         return pd.DataFrame()
#
#
# class TacticalOrchestrator:
#     def __init__(self, roster_df):
#         self.roster = roster_df.copy().reset_index(drop=True)
#         # Initialize Live Stats (Index=Player Name)
#         self.live_stats = pd.DataFrame(0.0, index=self.roster['Player'],
#                                        columns=['PTS', 'AST', 'ORB', 'DRB', 'TRB', 'STL', 'BLK', 'PF', 'TOV', 'MIN'])
#         self.translator = None
#         self.game_minutes = 0
#
#     def connect_brain(self, api_key):
#         """Initialize the AI translator with API key."""
#         try:
#             if not api_key or not api_key.strip():
#                 raise ValueError("API key cannot be empty")
#             self.translator = TacticalTranslator(api_key)
#         except Exception as e:
#             raise RuntimeError(f"Failed to connect translator: {str(e)}")
#
#     def update_tick(self, active_players):
#         """Simulate game time: updates minutes and random stat accumulation."""
#         if self.game_minutes >= 48:
#             return [] #Niv: False
#         self.game_minutes += 1
#         new_foul_outs = []
#         for name in active_players:
#             # Get player static data for variance base
#             p_data = self.roster[self.roster['Player'] == name].iloc[0]
#             avg_min = p_data['Avg minutes p'] if p_data['Avg minutes p'] > 0 else 10.0
#             mp_ratio = 1.0 / avg_min
#
#             self.live_stats.at[name, 'MIN'] += 1.0
#
#             # Accumulate stats based on avg/min + variance
#             for stat in ['PTS', 'AST', 'ORB', 'DRB', 'STL', 'BLK', 'TOV']:
#                 variance = np.random.normal(1.0, 0.25)
#                 val = (p_data.get(stat, 0) * mp_ratio) * variance
#                 self.live_stats.at[name, stat] += max(0, val)
#
#             # Update TRB
#             self.live_stats.at[name, 'TRB'] = self.live_stats.at[name, 'ORB'] + self.live_stats.at[name, 'DRB']
#
#             # Foul Simulation (Linear probability based on avg fouls)
#             if np.random.rand() < (p_data.get('PF', 2.0) / 30.0):
#                 self.live_stats.at[name, 'PF'] += 1
#             #niv
#                 # --- CRITICAL FIX ---
#                 # If player has 6+ fouls, ALWAYS add them to the list.
#                 # We removed the 'fouled_out_history' check because
#                 # if they are still in 'active_players', the crisis is not solved.
#             if self.live_stats.at[name, 'PF'] >= 6:
#                 new_foul_outs.append(name)
#
#         return new_foul_outs
#
#
# # ==========================================
# # POP-UP COMPONENT
# # ==========================================
# @st.dialog("🚨 TACTICAL INTERVENTION")
# def review_substitution_dialog():
#     if 'pending_sub' not in st.session_state or not st.session_state.pending_sub:
#         st.rerun()
#         return
#
#     proposal = st.session_state.pending_sub
#
#     # 1. The Explanation
#     st.markdown(f"**Coach's Eye:**")
#     st.info(proposal['explanation'])
#
#     # 2. The Visual Swap (Now with Images)
#     c1, c2, c3 = st.columns([1, 0.2, 1])
#
#     with c1:
#         st.markdown(f":green-background[**IN**]")
#
#         # Check for image
#         img_path = f"player_imgs/{proposal['sub_in']}.png"
#         if os.path.exists(img_path):
#             st.image(img_path, use_container_width=True)
#         else:
#             # Fallback placeholder if missing
#             st.image(f"https://placehold.co/150x150/F8F9FB/0068C9/png?text={proposal['sub_in'].split()[-1]}",
#                      use_container_width=True)
#
#         st.markdown(f"### :green[{proposal['sub_in']}]")
#
#     with c2:
#         st.markdown("<br><br><br><h1>🔄</h1>", unsafe_allow_html=True)
#
#     with c3:
#         st.markdown(f":red-background[**OUT**]")
#
#         # Check for image
#         img_path = f"player_imgs/{proposal['sub_out']}.png"
#         if os.path.exists(img_path):
#             st.image(img_path, use_container_width=True)
#         else:
#             # Fallback placeholder if missing
#             st.image(f"https://placehold.co/150x150/F8F9FB/FF4B4B/png?text={proposal['sub_out'].split()[-1]}",
#                      use_container_width=True)
#
#         st.markdown(f"### :red[{proposal['sub_out']}]")
#
#     st.divider()
#
#     # 3. Decision Buttons
#     col_accept, col_decline = st.columns(2)
#
#     with col_accept:
#         if st.button("✅ ACCEPT", type="primary", use_container_width=True):
#             if proposal['sub_out'] in st.session_state.active_lineup_names:
#                 st.session_state.active_lineup_names.remove(proposal['sub_out'])
#             st.session_state.active_lineup_names.append(proposal['sub_in'])
#
#             st.session_state.pending_sub = None
#             st.session_state.fouled_player = None
#             st.session_state.rejected_subs = []
#             st.session_state.last_exp = f"Sub Executed: {proposal['sub_in']} replaced {proposal['sub_out']}"
#             st.rerun()
#
#     with col_decline:
#         if st.button("❌ DECLINE", use_container_width=True):
#             if st.session_state.fouled_player is not None:
#                 st.session_state.rejected_subs.append(proposal['sub_in'])
#                 st.session_state.auto_solve = True
#                 st.session_state.pending_sub = None
#                 st.toast(f"Declined {proposal['sub_in']}. Finding alternative...", icon="🔄")
#                 st.rerun()
#             else:
#                 st.session_state.pending_sub = None
#                 st.rerun()
# # ==========================================
# # 2. MAIN APP CONTROLLER
# # ==========================================
# def main():
#     # 1. Apply Styles
#     styles.setup_page()
#
#     # 2. Session State Init
#     if 'game_active' not in st.session_state: st.session_state.game_active = False
#     if 'command_mode' not in st.session_state: st.session_state.command_mode = False
#     if 'auto_solve' not in st.session_state: st.session_state.auto_solve = False
#     if 'fouled_player' not in st.session_state: st.session_state.fouled_player = None
#     if 'pending_sub' not in st.session_state: st.session_state.pending_sub = None
#     if 'rejected_subs' not in st.session_state: st.session_state.rejected_subs = []
#
#     # --- NEW: GLOBAL LOCK LOGIC ---
#     # If a sub is pending, all background buttons become disabled
#     app_locked = st.session_state.pending_sub is not None
#     # ------------------------------
#
#     if st.session_state.pending_sub:
#         review_substitution_dialog()
#
#     # 3. Sidebar Logic
#     with st.sidebar:
#         st.title("🛡️ CORTEX CONTROL")
#         api_key = st.text_input("Gemini API Key", type="password", disabled=app_locked)  # Lock API input too
#         full_dataset = load_and_clean_data("player_stats.csv")
#
#         if not st.session_state.game_active:
#             if not full_dataset.empty:
#                 teams = sorted(full_dataset['Team'].dropna().unique())
#                 sel_team = st.selectbox("Select Team", teams, index=teams.index("SAC") if "SAC" in teams else 0,
#                                         disabled=app_locked)
#
#                 if st.button("🚀 INITIATE SESSION", disabled=app_locked):
#                     if api_key:
#                         try:
#                             team_roster = full_dataset[full_dataset['Team'] == sel_team]
#
#                             if team_roster.empty:
#                                 st.error(f"No players found for team: {sel_team}")
#                             else:
#                                 st.session_state.orch = TacticalOrchestrator(team_roster)
#                                 st.session_state.orch.connect_brain(api_key)
#
#                                 starters = team_roster.sort_values('Avg minutes p', ascending=False).head(5)
#                                 st.session_state.active_lineup_names = starters['Player'].tolist()
#
#                                 st.session_state.game_active = True
#                                 st.success(f"Session started for {sel_team}!")
#                                 st.rerun()
#                         except Exception as e:
#                             st.error(f"Error initializing session: {str(e)}")
#                     else:
#                         st.error("API Key Required")
#         else:
#             st.success("SESSION LIVE")
#             st.divider()
#             c1, c2 = st.columns(2)
#
#             # 👇 LOCKED
#             if c1.button("⏱️ +1 MIN", disabled=app_locked):
#                 fouled_out_list = st.session_state.orch.update_tick(st.session_state.active_lineup_names)
#                 if fouled_out_list:
#                     st.session_state.auto_solve = True
#                     st.session_state.fouled_player = fouled_out_list[0]
#                     st.session_state.command_mode = True
#                     st.toast(f"🚨Critical: {fouled_out_list[0]} Fouled out!", icon="⚠️")
#                     time.sleep(2)
#                 else:
#                     st.toast("Time Advanced")
#                 st.rerun()
#
#             # 👇 LOCKED
#             if c2.button("🛑 END", disabled=app_locked):
#                 st.session_state.game_active = False
#                 st.cache_data.clear()
#                 st.rerun()
#
#     # 4. Main Dashboard Logic
#     if st.session_state.game_active:
#
#         # A. Render Court
#         styles.render_court_view(
#             st.session_state.active_lineup_names,
#             st.session_state.orch.live_stats,
#             st.session_state.orch.roster
#         )
#
#         # B. War Room Logic
#         if not st.session_state.command_mode:
#             st.markdown('<span id="tactical-trigger-marker"></span>', unsafe_allow_html=True)
#
#             # 👇 LOCKED
#             if st.button("🧠 OPEN TACTICAL COMMAND", use_container_width=True, type="primary", disabled=app_locked):
#                 st.session_state.command_mode = True
#                 st.rerun()
#         else:
#             st.subheader("🧠 TACTICAL WAR ROOM")
#
#             if not st.session_state.auto_solve:
#                 st.info("👋 **Awaiting Orders:** Type a command below (e.g., 'Need more defense', 'Small ball lineup').")
#
#             # 👇 LOCKED (Chat Input)
#             coach_input = st.chat_input("Enter tactical directive...", disabled=app_locked)
#
#             # TRIGGERS: Chat Input OR Auto-Solve
#             if coach_input or st.session_state.auto_solve:
#                 with st.spinner("Analyzing Rotation..."):
#                     try:
#                         orch = st.session_state.orch
#
#                         # 1. Handle Auto-Solve vs Manual
#                         if st.session_state.auto_solve:
#                             fouled_p = st.session_state.fouled_player
#                             coach_input = f"Emergency: Replace {fouled_p} (Fouled Out)"
#                             target_stats = ["PF", "TOV", "STL", "BLK", "DRB"]
#                             st.session_state.auto_solve = False
#                         else:
#                             target_stats = orch.translator.translate(coach_input)
#
#                         # 2. Prepare Data
#                         df_for_solver = orch.roster.copy()
#                         df_for_solver['is_playing'] = df_for_solver['Player'].apply(
#                             lambda x: 1 if x in st.session_state.active_lineup_names else 0
#                         )
#
#                         processed_df = solver.prepare_solver_data(
#                             df_for_solver, orch.live_stats, target_stats
#                         )
#
#                         # 3. Run Solver
#                         solution = solver.optimize_single_flip(
#                             processed_df,
#                             max_fouls=6,
#                             force_out_player=fouled_p if 'fouled_p' in locals() else None,
#                             forbidden_players=st.session_state.rejected_subs
#                         )
#
#                         if solution:
#                             sub_in = solution['sub_in_player']
#                             sub_out = solution['sub_out_player']
#
#                             try:
#                                 explanation = orch.translator.explain_tactical_decision(
#                                     coach_input, [sub_in], [sub_out], solution['gap_vector']
#                                 )
#                             except:
#                                 explanation = f"Subbing {sub_in} for {sub_out} to optimize {target_stats}."
#
#                             st.session_state.pending_sub = {
#                                 "sub_in": sub_in,
#                                 "sub_out": sub_out,
#                                 "explanation": explanation,
#                                 "gap_vector": solution['gap_vector']
#                             }
#                             st.rerun()
#                         else:
#                             st.error("No valid substitution found.")
#
#                     except Exception as e:
#                         st.error(f"Error: {str(e)}")
#
#             # 👇 LOCKED
#             if st.button("✖️ CLOSE WAR ROOM", use_container_width=True, disabled=app_locked):
#                 st.session_state.command_mode = False
#                 st.rerun()
#
#         # C. Render Bench
#         styles.render_bench_table(
#             st.session_state.orch.live_stats,
#             st.session_state.active_lineup_names
#         )
#
#     else:
#         styles.render_offline_screen()
#
#
# if __name__ == "__main__":
#     main()

import streamlit as st
import pandas as pd
import numpy as np
import traceback
import time
import os
# Custom Modules
import solver
from translator import TacticalTranslator
import styles


# ==========================================
# 1. DATA & LOGIC ENGINE
# ==========================================
@st.cache_data
def load_and_clean_data(filepath):
    try:
        df = pd.read_csv(filepath)
        df.columns = [c.strip().replace('▲', '') for c in df.columns]

        col_map = {'Avg minutes played': 'Avg minutes p'}
        df = df.rename(columns=col_map)

        # Convert Positions column to list format
        def normalize_positions(pos):
            if pd.isnull(pos):
                return []
            if isinstance(pos, list):
                return [str(p).strip() for p in pos if pd.notnull(p)]
            # If it's a string, split by comma if multiple positions
            pos_str = str(pos).strip()
            if ',' in pos_str:
                return [p.strip() for p in pos_str.split(',') if p.strip()]
            return [pos_str] if pos_str else []

        df['Position'] = df['Position'].apply(normalize_positions)

        # Ensure numeric columns are actually numeric
        target_cols = ['PTS', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'Avg minutes p', 'ORB', 'DRB', 'TRB', '3P%', '2P%',
                       'eFG%', 'FT%']
        for col in target_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            else:
                df[col] = 0.0
        return df
    except Exception as e:
        st.error(f"Data Error: {e}")
        return pd.DataFrame()


class TacticalOrchestrator:
    def __init__(self, roster_df):
        self.roster = roster_df.copy().reset_index(drop=True)
        # Initialize Live Stats (Index=Player Name)
        self.live_stats = pd.DataFrame(0.0, index=self.roster['Player'],
                                       columns=['PTS', 'AST', 'ORB', 'DRB', 'TRB', 'STL', 'BLK', 'PF', 'TOV', 'MIN'])
        self.translator = None
        self.game_minutes = 0

    def connect_brain(self, api_key):
        """Initialize the AI translator with API key."""
        try:
            if not api_key or not api_key.strip():
                raise ValueError("API key cannot be empty")
            self.translator = TacticalTranslator(api_key)
        except Exception as e:
            raise RuntimeError(f"Failed to connect translator: {str(e)}")

    def update_tick(self, active_players):
        """Simulate game time: updates minutes and random stat accumulation."""
        if self.game_minutes >= 48:
            return []  # Niv: False
        self.game_minutes += 1
        new_foul_outs = []
        for name in active_players:
            # Get player static data for variance base
            p_data = self.roster[self.roster['Player'] == name].iloc[0]
            avg_min = p_data['Avg minutes p'] if p_data['Avg minutes p'] > 0 else 10.0
            mp_ratio = 1.0 / avg_min

            self.live_stats.at[name, 'MIN'] += 1.0

            # Accumulate stats based on avg/min + variance
            for stat in ['PTS', 'AST', 'ORB', 'DRB', 'STL', 'BLK', 'TOV']:
                variance = np.random.normal(1.0, 0.25)
                val = (p_data.get(stat, 0) * mp_ratio) * variance
                self.live_stats.at[name, stat] += max(0, val)

            # Update TRB
            self.live_stats.at[name, 'TRB'] = self.live_stats.at[name, 'ORB'] + self.live_stats.at[name, 'DRB']

            # Foul Simulation (Linear probability based on avg fouls)
            if np.random.rand() < (p_data.get('PF', 2.0) / 30.0):
                self.live_stats.at[name, 'PF'] += 1

            # Check Fouls
            if self.live_stats.at[name, 'PF'] >= 6:
                new_foul_outs.append(name)

        return new_foul_outs


# ==========================================
# POP-UP COMPONENT
# ==========================================
@st.dialog("🚨 TACTICAL INTERVENTION")
def review_substitution_dialog():
    if 'pending_sub' not in st.session_state or not st.session_state.pending_sub:
        st.rerun()
        return

    proposal = st.session_state.pending_sub

    # 1. The Explanation
    st.markdown(f"**Coach's Eye:**")
    st.info(proposal['explanation'])

    # 2. The Visual Swap (Now with Images)
    c1, c2, c3 = st.columns([1, 0.2, 1])

    with c1:
        st.markdown(f":green-background[**IN**]")
        img_path = f"player_imgs/{proposal['sub_in']}.png"
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.image(f"https://placehold.co/150x150/F8F9FB/0068C9/png?text={proposal['sub_in'].split()[-1]}",
                     use_container_width=True)
        st.markdown(f"### :green[{proposal['sub_in']}]")

    with c2:
        st.markdown("<br><br><br><h1>🔄</h1>", unsafe_allow_html=True)

    with c3:
        st.markdown(f":red-background[**OUT**]")
        img_path = f"player_imgs/{proposal['sub_out']}.png"
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.image(f"https://placehold.co/150x150/F8F9FB/FF4B4B/png?text={proposal['sub_out'].split()[-1]}",
                     use_container_width=True)
        st.markdown(f"### :red[{proposal['sub_out']}]")

    st.divider()

    # 3. Decision Buttons
    col_accept, col_decline = st.columns(2)

    # ... inside col_accept ...
    with col_accept:
        if st.button("✅ ACCEPT", type="primary", use_container_width=True):
            if proposal['sub_out'] in st.session_state.active_lineup_names:
                st.session_state.active_lineup_names.remove(proposal['sub_out'])
            st.session_state.active_lineup_names.append(proposal['sub_in'])

            current_time = st.session_state.orch.game_minutes

            # 1. Bench Cooldown: Player leaving cannot return for 8 mins
            st.session_state.sub_cooldowns[proposal['sub_out']] = current_time + 8

            # 2. 👇 NEW Entry Protection: Player entering cannot leave for 8 mins
            st.session_state.entry_protection[proposal['sub_in']] = current_time + 8

            st.session_state.pending_sub = None
            st.session_state.fouled_player = None
            st.session_state.rejected_subs = []
            st.session_state.last_exp = f"Sub Executed: {proposal['sub_in']} replaced {proposal['sub_out']}"
            st.rerun()

    with col_decline:
        if st.button("❌ DECLINE", use_container_width=True):
            if st.session_state.fouled_player is not None:
                st.session_state.rejected_subs.append(proposal['sub_in'])
                st.session_state.auto_solve = True
                st.session_state.pending_sub = None
                st.toast(f"Declined {proposal['sub_in']}. Finding alternative...", icon="🔄")
                st.rerun()
            else:
                st.session_state.pending_sub = None
                st.rerun()


# ==========================================
# 2. MAIN APP CONTROLLER
# ==========================================
# ==========================================
# 2. MAIN APP CONTROLLER
# ==========================================
# ==========================================
# 2. MAIN APP CONTROLLER
# ==========================================
def main():
    # 1. Apply Styles
    styles.setup_page()

    # 2. Session State Init
    if 'game_active' not in st.session_state: st.session_state.game_active = False
    if 'command_mode' not in st.session_state: st.session_state.command_mode = False
    if 'auto_solve' not in st.session_state: st.session_state.auto_solve = False
    if 'fouled_player' not in st.session_state: st.session_state.fouled_player = None
    if 'pending_sub' not in st.session_state: st.session_state.pending_sub = None
    if 'rejected_subs' not in st.session_state: st.session_state.rejected_subs = []

    # 👇 NEW: Track when players can return
    if 'sub_cooldowns' not in st.session_state: st.session_state.sub_cooldowns = {}

    # 👇 NEW: Track players who just entered the court
    if 'entry_protection' not in st.session_state: st.session_state.entry_protection = {}
    # --- GLOBAL LOCK LOGIC ---
    app_locked = st.session_state.pending_sub is not None

    if st.session_state.pending_sub:
        review_substitution_dialog()

    # ==========================================
    # VIEW A: SETUP SCREEN (SIDEBAR VISIBLE)
    # ==========================================
    if not st.session_state.game_active:
        with st.sidebar:
            st.title("🛡️ CORTEX CONTROL")
            api_key = st.text_input("User Name", type="password")
            api_key = st.secrets["GEMINI_API_KEY"]
            full_dataset = load_and_clean_data("player_stats.csv")

            if not full_dataset.empty:
                teams = sorted(full_dataset['Team'].dropna().unique())
                sel_team = st.selectbox("Select Team", teams, index=teams.index("SAC") if "SAC" in teams else 0)

                st.markdown("---")
                if st.button("🚀 INITIATE SESSION", use_container_width=True):
                    if api_key:
                        try:
                            team_roster = full_dataset[full_dataset['Team'] == sel_team]
                            if team_roster.empty:
                                st.error(f"No players found for team: {sel_team}")
                            else:
                                st.session_state.orch = TacticalOrchestrator(team_roster)
                                st.session_state.orch.connect_brain(api_key)

                                starters = team_roster.sort_values('Avg minutes p', ascending=False).head(5)
                                st.session_state.active_lineup_names = starters['Player'].tolist()

                                st.session_state.game_active = True
                                st.success(f"Session started for {sel_team}!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error initializing session: {str(e)}")
                    else:
                        st.error("API Key Required")

        styles.render_offline_screen()

    # ==========================================
    # VIEW B: LIVE GAME (SIDEBAR GONE)
    # ==========================================
    else:
        # 1. TOP CONTROL BAR
        with st.container():
            c_info, c_spacer, c_controls = st.columns([3, 3, 4])

            with c_info:
                current_min = st.session_state.orch.game_minutes
                if current_min >= 48:
                    status_display = "GAME OVER!"
                else:
                    status_display = f"Q{(current_min // 12) + 1}"

                st.markdown(f"### ⏱️ MIN: {current_min} | {status_display}")
            with c_controls:
                b1, b2 = st.columns(2)

                # ... [Inside main() -> c_controls -> +1 MIN button] ...
                if b1.button("⏱️ +1 MIN", disabled=app_locked, use_container_width=True):
                    # 1. Advance Time
                    fouled_out_list = st.session_state.orch.update_tick(st.session_state.active_lineup_names)

                    # 2. Check Scenario A: CRITICAL FOUL OUT
                    if fouled_out_list:
                        st.session_state.auto_solve = True
                        st.session_state.fouled_player = fouled_out_list[0]
                        st.session_state.command_mode = True
                        st.toast(f"🚨Critical: {fouled_out_list[0]} Fouled out!", icon="⚠️")
                        time.sleep(2)
                        st.rerun()

                        # ... (Inside the +1 MIN button logic) ...

                        # 3. Check Scenario B: 5-MINUTE SCHEDULED ROTATION
                    elif st.session_state.orch.game_minutes > 0 and st.session_state.orch.game_minutes % 5 == 0:
                        st.toast("🔄 Scheduled Rotation: Analyzing Bench...", icon="⏱️")

                        target_stats = ["PTS", "AST", "TRB", "PF", "STL"]
                        orch = st.session_state.orch

                        # 1. Calc Forbidden (Bench Cooldown)
                        cooldown_ban_list = [
                            name for name, ready_time in st.session_state.sub_cooldowns.items()
                            if orch.game_minutes < ready_time
                        ]
                        full_forbidden_list = st.session_state.rejected_subs + cooldown_ban_list

                        # 2. Calc Protected (Entry Protection)
                        protected_list = [
                            name for name, release_time in st.session_state.entry_protection.items()
                            if orch.game_minutes < release_time
                        ]

                        # B. Prepare Data
                        df_for_solver = orch.roster.copy()
                        df_for_solver['is_playing'] = df_for_solver['Player'].apply(
                            lambda x: 1 if x in st.session_state.active_lineup_names else 0
                        )

                        processed_df = solver.prepare_solver_data(
                            df_for_solver, orch.live_stats, target_stats
                        )

                        # C. Run Solver
                        solution = solver.optimize_single_flip(
                            processed_df,
                            max_fouls=6,
                            forbidden_players=full_forbidden_list,
                            protected_players=protected_list
                        )

                        # D. Trigger Pop-up
                        if solution:
                            sub_in = solution['sub_in_player']
                            sub_out = solution['sub_out_player']

                            # 👇👇👇 NEW: ASK AI FOR RICH EXPLANATION 👇👇👇
                            # We create a "synthetic" query to tell the AI what's happening
                            simulated_query = (
                                f"Automatic rotation at minute {orch.game_minutes}. "
                                f"{sub_out} is fatigued. Subbing in {sub_in} to improve {', '.join(target_stats[:3])}."
                            )

                            try:
                                # Use the AI Brain to generate the message
                                explanation = orch.translator.explain_tactical_decision(
                                    simulated_query, [sub_in], [sub_out], solution['gap_vector']
                                )
                            except Exception:
                                # Fallback if AI fails or is offline
                                explanation = f"⏱️ **Scheduled Rotation:** Substituting {sub_in} for {sub_out} to manage fatigue and maintain defensive intensity."

                            st.session_state.pending_sub = {
                                "sub_in": sub_in,
                                "sub_out": sub_out,
                                "explanation": explanation,  # 👈 Now contains the AI text
                                "gap_vector": solution['gap_vector']
                            }
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.toast("Time Advanced (Lineup Optimal)", icon="✅")
                            st.rerun()
                    # 4. Standard Advance
                    else:
                        st.toast("Time Advanced")
                        st.rerun()

                if b2.button("🛑 END GAME", disabled=app_locked, use_container_width=True):
                    st.session_state.game_active = False
                    st.cache_data.clear()
                    st.rerun()

        st.divider()

        # 2. MAIN GAME VIEW

        # --- PART A: THE BUTTON (Appears ABOVE players when closed) ---
        if not st.session_state.command_mode:
            st.markdown('<span id="tactical-trigger-marker"></span>', unsafe_allow_html=True)
            if st.button("🧠 OPEN TACTICAL COMMAND", use_container_width=True, type="primary", disabled=app_locked):
                st.session_state.command_mode = True
                st.rerun()

        # --- PART B: THE PLAYERS (Always in the Middle) ---
        styles.render_court_view(
            st.session_state.active_lineup_names,
            st.session_state.orch.live_stats,
            st.session_state.orch.roster
        )

        # --- PART C: THE WAR ROOM (Appears BELOW players when open) ---
        if st.session_state.command_mode:
            st.subheader("🧠 TACTICAL WAR ROOM")
            if not st.session_state.auto_solve:
                st.info("👋 **Awaiting Orders:** Type a command in the chat below (e.g., 'Need more defense', 'Small ball lineup').")

            coach_input = st.chat_input("Enter tactical directive...", disabled=app_locked)

            if coach_input or st.session_state.auto_solve:
                with st.spinner("Analyzing Rotation..."):
                    try:
                        orch = st.session_state.orch
                        if st.session_state.auto_solve:
                            fouled_p = st.session_state.fouled_player
                            coach_input = f"Emergency: Replace {fouled_p} (Fouled Out)"
                            target_stats = ["PF", "TOV", "STL", "BLK", "DRB"]
                            st.session_state.auto_solve = False
                        else:
                            target_stats = orch.translator.translate(coach_input)

                        df_for_solver = orch.roster.copy()
                        df_for_solver['is_playing'] = df_for_solver['Player'].apply(
                            lambda x: 1 if x in st.session_state.active_lineup_names else 0
                        )

                        processed_df = solver.prepare_solver_data(
                            df_for_solver, orch.live_stats, target_stats
                        )

                        solution = solver.optimize_single_flip(
                            processed_df,
                            max_fouls=6,
                            force_out_player=fouled_p if 'fouled_p' in locals() else None,
                            forbidden_players=st.session_state.rejected_subs
                        )

                        if solution:
                            sub_in = solution['sub_in_player']
                            sub_out = solution['sub_out_player']
                            try:
                                explanation = orch.translator.explain_tactical_decision(
                                    coach_input, [sub_in], [sub_out], solution['gap_vector']
                                )
                            except:
                                explanation = f"Subbing {sub_in} for {sub_out} to optimize {target_stats}."

                            st.session_state.pending_sub = {
                                "sub_in": sub_in,
                                "sub_out": sub_out,
                                "explanation": explanation,
                                "gap_vector": solution['gap_vector']
                            }
                            st.rerun()
                        else:
                            st.error("No valid substitution found.")

                    except Exception as e:
                        st.error(f"Error: {str(e)}")

            if st.button("✖️ CLOSE WAR ROOM", use_container_width=True, disabled=app_locked):
                st.session_state.command_mode = False
                st.rerun()

        # D. Render Bench
        styles.render_bench_table(
            st.session_state.orch.live_stats,
            st.session_state.active_lineup_names
        )


if __name__ == "__main__":
    main()