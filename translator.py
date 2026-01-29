import google.generativeai as genai
import json
import re
import streamlit as st
import vertexai
from vertexai.generative_models import GenerativeModel


class TacticalTranslator:
    def __init__(self, api_key):
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')

            # VOCABULARY
            self.available_stats = [
                "Player", "Age", "Team", "Position", "Games", "Games Started",
                "Avg minutes played", "Avg field goal", "Avg field goal attempts",
                "Field goal percentage", "avg three points made", "3PA", "3P%",
                "2P", "2PA", "2P%", "eFG%", "FT", "FTA", "FT%", "ORB", "DRB",
                "TRB", "AST", "STL", "BLK", "PF", "PTS",
                "Live minutes played", "Live field goal attempts", "Live Field goal percentage",
                "Live 3PA", "Live 3PM", "Live 3p%", "Live 2PA", "Live 2PM", "Live 2P%",
                "Live FTA", "Live FTM", "Live FT%", "Live ORB", "Live DRB", "Live TRB",
                "Live AST", "Live STL", "Live BLK", "Live PF", "Live PTS"
            ]
        except Exception as e:
            print(f"AI Config Error: {e}")

    def translate(self, natural_language_command):
        """
        Translates commands into stats, but handles 'Optimization Logic'.
        Since the solver MAXIMIZES sums, we must map 'avoid negative things'
        to 'maximize positive proxies'.
        """
        prompt = f"""
        You are the Tactical Cortex (Brain) for an NBA Analytics Engine.
        Your goal is to convert a Coach's voice command into a list of statistical categories to MAXIMIZE.
        You achieve that goal by selecting the most fitting subset of available stats, and them only!
        to select the subset you can rate importance of each stat from 0-1 and take the top ones or those who pass a certain percentage.

        Available Stats: {self.available_stats}

        CRITICAL LOGIC:
        1. The solver MAXIMIZES the stats you return, PF changed to be maximized as well
        2. Find the relevant stats and their "live" counter part if exists.
        3. If the coach says "Stop Fouling", do NOT return "PF". Return "STL" (Clean defense) or "BLK".
        4. If the coach says "Defense", combine "STL", "BLK", "DRB".
        5. "If the coach uses words like "now", "lately" or "right now" prioritize Live stats. If the coach asks for a general change, use Avg stats."
        6. VOLUME VS EFFICIENCY: When asking for scoring, always include "eFG%" or "3P%" alongside "PTS" to ensure quality over quantity.
        7. SIZE PROXIES: Use "BLK" and "DRB" as the primary stats for "Size" or "Interior presence".
        8. BALL MOVEMENT: "AST" and "Live AST" are the only metrics for ball movement; use them if the coach mentions "ISO" or "Ball hogging".
        9. THE SPACING RULE: If the coach mentions "Space" or "Gravity", prioritize "3PA" (Volume of threats) and "3P%" (Accuracy of threats).
     

        Examples:
        - "We need buckets now!" -> ["PTS", "3P%", "eFG%"]
        - "We are getting killed on the glass." -> ["DRB", "TRB"]
        - "They’re living in the paint. Get me some rim protection." -> ["BLK", "DRB"]
        - "Take care of the ball, too many mistakes." -> ["AST", "eFG%"] (Proxies for safety)
        - "We need energy and hustle." -> ["ORB", "STL", "BLK"]
        - "The floor is too shrunk. We need more gravity." -> ["avg three points made", "3PA", "3P%"]

        Coach Command: "{natural_language_command}"

        Return ONLY a JSON list of strings. No markdown.
        """
        try:
            response = self.model.generate_content(prompt)
            # Robust JSON cleaning
            clean_text = response.text.strip()
            # Use regex to find the list brackets in case of extra text
            match = re.search(r'\[.*?\]', clean_text, re.DOTALL)
            if match:
                clean_text = match.group(0)

            stats = json.loads(clean_text)

            # Validation
            # Validation
            valid_stats = [s for s in stats if s in self.available_stats]

            if not valid_stats:
                # This prints to your console so you know the AI failed/hallucinated
                print("WARNING: Tactical Cortex failed to map command. Defaulting to ['PTS'].")
                return ["PTS"]

            return valid_stats

        except Exception as e:
            print(f"Translation logic error: {e}")
            return ["PTS"]

    def explain_tactical_decision(self, command, players_in, players_out, stat_diff):
        """
        Generates a contextual explanation that weighs the trade-offs.
        """
        # Convert diffs to a string description for the AI to analyze magnitude
        diff_context = ", ".join([f"{k}: {v}" for k, v in stat_diff.items()])

        prompt = f"""
        You are an elite NBA Head Coach (like Gregg Popovich or Erik Spoelstra or Steve Kerr) in a timeout.
        Analyze this substitution proposal.

        Context:
        - The Coach's Demand is: "{command}"
        - Subbing IN: {', '.join(players_in)}
        - Subbing OUT: {', '.join(players_out)}
        - Net Stat Changes: {diff_context}

        Task:
        Write a 2 to 3 sentence explanation to your assistants.
        1. Acknowledge the trade-off (what we lose vs what we gain) by going over each element in {diff_context}.
        2. If a stat gain/loss is small (e.g. +0.1), treat it as negligible. If large (e.g. +5.0 or +10%), emphasize it.
            2.1 use basketball logic also to reassure if a stat is negligible or not
        3. then choose the most important ones, for good and for bad.
        4. Use basketball terminology (spacing, verticality, ball pressure, rim protection) to incorporate it to 1-2 sentences
        
        
        Example Format:
        "I'm suggesting to sub in [Players_in] for [Players_out],
         We give up some [proper term lost], but the boost in [proper term Gained] solves the [Command] issue.
         the main changes are: [the positive gaps by name and value] and [the negative gaps by name and value]"
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"{e} \n Subbing {', '.join(players_in)} for {', '.join(players_out)}."