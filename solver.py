from ortools.sat.python import cp_model
import pandas as pd
import numpy as np


def prepare_solver_data(avg_df, live_stats_df, stats_to_maximize):
    """
    Step 1: Data Preprocessing & Scoring.
    Combines static skill (avg_df) with live constraints (live_stats_df).
    """
    # 1. Merge Static and Live Data
    # We assume both DFs are aligned by index or Player name.
    # For safety, we use the Static DF as the base and update specific columns from Live DF.
    live_df = live_stats_df.copy()
    avg_df = avg_df.copy()
    # Join static and live stats; suffixes ensure we keep both (e.g., PTS vs PTS_live)
    live_df = live_df.reset_index().rename(columns={'index': 'Player'})
    df = pd.merge(avg_df, live_df, on='Player', how='left', suffixes=('', '_live'))

    # Explicitly set the constraint columns to use Live data, falling back to static if missing
    df['PF'] = df.get('PF_live', df.get('PF'))
    df['MIN'] = df.get('MIN_live', 0.0)

    # 2. Normalization [0, 1]
    # Only process numeric columns requested by the coach
    cols_to_process = [c for c in stats_to_maximize if c in df.columns and '%' not in c]

    for col in cols_to_process:
        min_val = df[col].min()
        max_val = df[col].max()
        if max_val - min_val != 0:
            df[col] = (df[col] - min_val) / (max_val - min_val)
        else:
            df[col] = 0.0

    # 3. Foul Penalty (Minimize Fouls)
    # We keep a raw copy for the hard constraint
    if 'PF' in df.columns:
        # Normalized: 0 fouls = 1.0 score, 6 fouls = 0.0 score
        df['PF'] = 1.0 + (df['PF'] * -1.0 / 6.0)


    # 4. Fatigue Factor
    def calculate_tired_factor(minutes):
        if minutes < 10.0:
            return 1.0
        # Logarithmic decay: more minutes = lower factor
        return 1.0 / np.log10(minutes)

    if 'MIN' in df.columns:
        df['tired_factor'] = df['MIN'].apply(calculate_tired_factor)
    else:
        df['tired_factor'] = 1.0

    # 5. Position Mapping (List of Floats)
    pos_map = {"PG": 0.0, "SG": 0.25, "SF": 0.5, "PF": 0.75, "C": 1.0}

    def map_positions(row):
        # Handle cases where Positions might be a list or a string
        if isinstance(row, list):
            return [pos_map.get(p, 0.5) for p in row]
        return [0.5]  # Default to 0.5 if data is missing

    # Use 'Position' as standardized in app.py
    if 'Position' in df.columns:
        df['Position'] = df['Position'].apply(map_positions)
    else:
        # Fallback if column missing
        df['Position'] = [[0.5] for _ in range(len(df))]

    # 6. Apply Fatigue & Calculate Solver Score
    for stat in stats_to_maximize:
        if stat in df.columns:
            df[stat] = df[stat] * df['tired_factor']

    # Composite Score: Sum of weighted stats + Foul Score
    # We sum the normalized values for the objective function
    df['solver_score'] = df[stats_to_maximize].sum(axis=1) + df['PF']

    return df


# solver.py

def prepare_solver_data(avg_df, live_stats_df, stats_to_maximize):
    # [Keep Step 1 & 2 exactly the same...]
    live_df = live_stats_df.copy()
    avg_df = avg_df.copy()
    df = pd.merge(avg_df, live_df, on='Player', how='left', suffixes=('', '_live'))

    df['PF'] = df.get('PF_live', df.get('PF'))
    df['MIN'] = df.get('MIN_live', 0.0)

    # --- BUG FIX START: Save Raw Fouls BEFORE Normalization ---
    df['PF_raw'] = df['PF'].copy()
    # --------------------------------------------------------

    # 2. Normalization [0, 1]
    cols_to_process = [c for c in stats_to_maximize if c in df.columns and '%' not in c]
    for col in cols_to_process:
        min_val = df[col].min()
        max_val = df[col].max()
        if max_val - min_val != 0:
            df[col] = (df[col] - min_val) / (max_val - min_val)
        else:
            df[col] = 0.0

    # 3. Foul Penalty (Score Calculation)
    if 'PF' in df.columns:
        df['PF'] = 1.0 + (df['PF'] * -1.0 / 6.0)  # Now 'PF' is a score, but 'PF_raw' exists

    # [Keep Step 4, 5, 6 exactly the same...]
    def calculate_tired_factor(minutes):
        if minutes < 10.0: return 1.0
        if minutes >= 40.0: return 0.1 #extreme fatigue
        return 1.0 / np.log10(2.5*minutes)

    df['tired_factor'] = df['MIN'].apply(calculate_tired_factor) if 'MIN' in df.columns else 1.0

    pos_map = {"PG": 0.0, "SG": 0.25, "SF": 0.5, "PF": 0.75, "C": 1.0}

    def map_positions(row):
        if isinstance(row, list): return [pos_map.get(p, 0.5) for p in row]
        return [0.5]

    if 'Position' in df.columns:
        df['Position'] = df['Position'].apply(map_positions)
    else:
        df['Position'] = [[0.5] for _ in range(len(df))]

    for stat in stats_to_maximize:
        if stat in df.columns:
            df[stat] = df[stat] * df['tired_factor']

    df['solver_score'] = df[stats_to_maximize].sum(axis=1) + df['PF']

    return df


def optimize_single_flip(processed_df, max_fouls=6, force_out_player=None, forbidden_players=None,
                         protected_players=None):
    """
    Updates:
    - forbidden_players: List of names that cannot be subbed IN (Bench Cooldown).
    - protected_players: List of names that cannot be subbed OUT (Entry Protection).
    """
    if forbidden_players is None: forbidden_players = []
    if protected_players is None: protected_players = []  # 👈 Init new list

    model = cp_model.CpModel()

    players = []
    for idx, row in processed_df.iterrows():
        p_data = {
            'name': row['Player'],
            'score': int(row['solver_score'] * 1000),
            'is_playing': int(row['is_playing']),
            'fouls': row.get('PF_raw', 0),
            'pos_val': row['Position'][0] if len(row['Position']) > 0 else 0.5,
            'idx': idx
        }
        players.append(p_data)

    x = [model.NewBoolVar(f"x_{p['name']}") for p in players]
    is_in = [model.NewBoolVar(f"in_{p['name']}") for p in players]
    is_out = [model.NewBoolVar(f"out_{p['name']}") for p in players]

    # 1. Team Size
    model.Add(sum(x) == 5)

    # 2. Foul Constraints & Manual Overrides
    for i, p in enumerate(players):
        # A. General Rule (Fouled Out)
        if p['fouls'] >= max_fouls:
            model.Add(x[i] == 0)

        # B. Force Out (Critical)
        if force_out_player and p['name'] == force_out_player:
            model.Add(x[i] == 0)

        # C. Forbidden Substitutes (Bench Cooldown - Cannot come IN)
        if p['name'] in forbidden_players:
            model.Add(is_in[i] == 0)

        # D. Protected Players (Entry Protection - Cannot go OUT)
        # 👇 NEW LOGIC HERE 👇
        if p['name'] in protected_players:
            model.Add(is_out[i] == 0)

    # 3. Transition Logic
    for i, p in enumerate(players):
        model.Add(x[i] == p['is_playing'] + is_in[i] - is_out[i])
        if p['is_playing'] == 1:
            model.Add(is_in[i] == 0)
        else:
            model.Add(is_out[i] == 0)

    model.Add(sum(is_in) == 1)
    model.Add(sum(is_out) == 1)

    # ... (Rest of the function remains exactly the same: Penalty calc, Solve, Result) ...

    total_perf = sum(x[i] * p['score'] for i, p in enumerate(players))
    penalty_weight = 2500
    total_penalty = 0

    for i in range(len(players)):
        for j in range(len(players)):
            if players[i]['is_playing'] == 1: continue
            if players[j]['is_playing'] == 0: continue

            dist = abs(players[i]['pos_val'] - players[j]['pos_val'])
            p_val = int(dist * penalty_weight)
            pair_active = model.NewBoolVar(f"pair_{i}_{j}")
            model.AddBoolAnd([is_in[i], is_out[j]]).OnlyEnforceIf(pair_active)
            model.AddBoolOr([is_in[i].Not(), is_out[j].Not()]).OnlyEnforceIf(pair_active.Not())
            total_penalty += (pair_active * p_val)

    model.Maximize(total_perf - total_penalty)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        result = {}
        for i, p in enumerate(players):
            if solver.Value(is_in[i]):
                result['sub_in'] = p['name']
                result['sub_in_player'] = processed_df.loc[p['idx'], 'Player']
                sub_in_idx = p['idx']
            if solver.Value(is_out[i]):
                result['sub_out'] = p['name']
                result['sub_out_player'] = processed_df.loc[p['idx'], 'Player']
                sub_out_idx = p['idx']

        in_rec = processed_df.loc[sub_in_idx]
        out_rec = processed_df.loc[sub_out_idx]
        gap_vector = {}
        for col in processed_df.columns:
            if pd.api.types.is_numeric_dtype(processed_df[col]):
                gap_vector[col] = round(float(in_rec[col] - out_rec[col]), 4)
            else:
                gap_vector[col] = in_rec[col]
        result['gap_vector'] = gap_vector
        return result

    return None