import http.server
import socketserver
import json
import csv
import math
from collections import defaultdict

MODEL = None
FIGHTER_STATS = {}
WEIGHT_CLASS_DATA = {}

FEATURE_DESCRIPTIONS = {
    'HeightDif': 'height', 'ReachDif': 'reach', 'AgeDif': 'age', 'WinStreakDif': 'win streak',
    'LossDif': 'loss record', 'SigStrDif': 'significant strikes', 'AvgTDDif': 'takedowns',
    'TotalRoundDif': 'experience', 'TotalTitleBoutDif': 'championship experience', 
    'WeightDif': 'weight', 'RankDif': 'fighter rank'
}

def to_float(value, default=0.0):
    try: return float(value)
    except (ValueError, TypeError): return default

def get_rank(rank_str, unranked_value=20):
    if rank_str == 'C': return 0
    try: return float(rank_str)
    except (ValueError, TypeError): return unranked_value

def load_data():
    global MODEL, FIGHTER_STATS, WEIGHT_CLASS_DATA
    print("Loading model and performing advanced data pre-processing...")
    try:
        with open('model.json', 'r') as f: MODEL = json.load(f)
        all_fights = list(csv.DictReader(open('ufc-master.csv', 'r')))
        temp_fighter_stats = {}
        for row in all_fights:
            for corner in ['Red', 'Blue']:
                fighter_name = row[f'{corner}Fighter'].strip()
                if fighter_name and fighter_name not in temp_fighter_stats:
                    rank_key = 'RMatchWCRank' if corner == 'Red' else 'BMatchWCRank'
                    temp_fighter_stats[fighter_name] = {
                        'Name': fighter_name, 'WeightClass': row['WeightClass'], 'MatchWCRank': row[rank_key],
                        'HeightCms': row[f'{corner}HeightCms'], 'ReachCms': row[f'{corner}ReachCms'], 'Age': row[f'{corner}Age'], 'Stance': row[f'{corner}Stance'],
                        'CurrentWinStreak': row[f'{corner}CurrentWinStreak'], 'Losses': row[f'{corner}Losses'], 'AvgSigStrLanded': row[f'{corner}AvgSigStrLanded'],
                        'AvgTDLanded': row[f'{corner}AvgTDLanded'], 'TotalRoundsFought': row[f'{corner}TotalRoundsFought'], 'TotalTitleBouts': row[f'{corner}TotalTitleBouts'],
                        'AvgSigStrPct': row[f'{corner}AvgSigStrPct'], 'AvgTDPct': row[f'{corner}AvgTDPct'], 'AvgSubAtt': row[f'{corner}AvgSubAtt'],
                        'Wins': row[f'{corner}Wins'], 'Odds': row[f'{corner}Odds'], 'WeightLbs': row[f'{corner}WeightLbs']
                    }
        for fighter_name in temp_fighter_stats:
            ranked_wins = 0
            for fight in all_fights:
                if (fight['RedFighter'] == fighter_name and fight['Winner'] == 'Red' and get_rank(fight['BMatchWCRank']) <= 15) or \
                   (fight['BlueFighter'] == fighter_name and fight['Winner'] == 'Blue' and get_rank(fight['RMatchWCRank']) <= 15):
                    ranked_wins += 1
            temp_fighter_stats[fighter_name]['RankedWins'] = ranked_wins
        FIGHTER_STATS = temp_fighter_stats
        for name, stats in FIGHTER_STATS.items():
            wc = stats.get('WeightClass')
            if wc and 'Women' not in wc:
                if wc not in WEIGHT_CLASS_DATA: WEIGHT_CLASS_DATA[wc] = []
                WEIGHT_CLASS_DATA[wc].append(name)
        print("Data loaded successfully.")
    except FileNotFoundError as e: print(f"Error loading data: {e}"); MODEL = None

def predict_winner(red_fighter_name, blue_fighter_name):
    print(f"\n--- PREDICTION REQUEST: {red_fighter_name} vs {blue_fighter_name} ---")
    if not MODEL or not FIGHTER_STATS: print("DEBUG: Model or stats not loaded."); return {"error": "Model or fighter data not loaded."}
    
    print("DEBUG: Getting fighter stats...")
    red_stats = FIGHTER_STATS.get(red_fighter_name)
    blue_stats = FIGHTER_STATS.get(blue_fighter_name)
    if not red_stats or not blue_stats: print("DEBUG: Fighter stats not found."); return {"error": "One or both fighters not found."}

    weights = MODEL['weights']; scaling_params = MODEL['scaling_params']; z = MODEL['bias']
    feature_vector = {}; feature_contributions = {}
    
    print("DEBUG: Starting feature engineering...")
    try:
        diff_attrs = {
            'WeightDif': 'WeightLbs', 'HeightDif': 'HeightCms', 'ReachDif': 'ReachCms', 'AgeDif': 'Age',
            'LossDif': 'Losses', 'SigStrDif': 'AvgSigStrLanded',
            'AvgTDDif': 'AvgTDLanded', 'TotalRoundDif': 'TotalRoundsFought', 'TotalTitleBoutDif': 'TotalTitleBouts'
        }
        for key, attr in diff_attrs.items(): feature_vector[key] = to_float(red_stats.get(attr)) - to_float(blue_stats.get(attr))
        feature_vector['RankDif'] = get_rank(red_stats.get('MatchWCRank')) - get_rank(blue_stats.get('MatchWCRank'))
        raw_features = ['AvgSigStrLanded', 'AvgSigStrPct', 'AvgTDLanded', 'AvgTDPct', 'AvgSubAtt', 'Wins', 'Losses', 'Odds']
        for feat in raw_features: feature_vector[f'Red{feat}'] = to_float(red_stats.get(feat)); feature_vector[f'Blue{feat}'] = to_float(blue_stats.get(feat))
        for f_name in weights.keys():
            if f_name.startswith('RedStance_'): feature_vector[f_name] = 1 if red_stats.get('Stance') == f_name.replace('RedStance_', '') else 0
            elif f_name.startswith('BlueStance_'): feature_vector[f_name] = 1 if blue_stats.get('Stance') == f_name.replace('BlueStance_', '') else 0
        print("DEBUG: Feature engineering successful.")
    except Exception as e: print(f"DEBUG: CRASH during feature engineering: {e}"); return {"error": f"Could not create feature for prediction. Error: {e}"}

    print("DEBUG: Starting prediction calculation...")
    for feature, value in feature_vector.items():
        if feature in weights and feature in scaling_params:
            scaled_value = (value - to_float(scaling_params[feature].get('mean'))) / to_float(scaling_params[feature].get('std_dev'), default=1)
            contribution = weights[feature] * scaled_value
            z += contribution
            feature_contributions[feature] = contribution

    prob_red_wins = 1 / (1 + math.exp(-z))
    winner = red_fighter_name if prob_red_wins > 0.5 else blue_fighter_name
    confidence = prob_red_wins if winner == red_fighter_name else 1 - prob_red_wins
    print("DEBUG: Prediction calculation successful.")

    print("DEBUG: Starting explanation generation...")
    try:
        diff_features = {k: v for k, v in feature_contributions.items() if 'Dif' in k}
        sorted_diffs = sorted(diff_features.items(), key=lambda item: abs(item[1]), reverse=True)
        top_features = sorted_diffs[:3]
        if not top_features:
            main_point = "The model could not identify a single dominant factor for this prediction."
            details = []
        else:
            main_factor = top_features[0]
            main_point = f"The model's prediction hinges on a significant {FEATURE_DESCRIPTIONS.get(main_factor[0], main_factor[0])} advantage for {red_fighter_name if main_factor[1] > 0 else blue_fighter_name}."
            details = [f"A secondary factor was a {FEATURE_DESCRIPTIONS.get(f, f)} advantage for {red_fighter_name if c > 0 else blue_fighter_name}." for f, c in top_features[1:]]

        red_wins = to_float(red_stats.get('Wins')); red_losses = to_float(red_stats.get('Losses'))
        blue_wins = to_float(blue_stats.get('Wins')); blue_losses = to_float(blue_stats.get('Losses'))
        details.insert(0, f"{red_fighter_name} holds a record of {int(red_wins)}-{int(red_losses)}, while {blue_fighter_name} is {int(blue_wins)}-{int(blue_losses)}.")
        red_ranked_wins = red_stats.get('RankedWins', 0)
        blue_ranked_wins = blue_stats.get('RankedWins', 0)
        if red_ranked_wins != blue_ranked_wins:
            details.append(f"In terms of schedule strength, {red_fighter_name} has {red_ranked_wins} wins against ranked opponents compared to {blue_ranked_wins} for {blue_fighter_name}.")
        print("DEBUG: Explanation generation successful.")
    except Exception as e: print(f"DEBUG: CRASH during explanation generation: {e}"); return {"error": f"Explanation generation failed. Error: {e}"}

    result = {"PredictedWinner": winner, "Confidence": f"{confidence * 100:.2f}%", "explanation": {"main_point": main_point, "details": details}}
    print(f"DEBUG: Successfully built final result object. Returning...\n{result}")
    return result

class PredictionServer(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/weightclasses': self.send_response(200); self.send_header('Content-type', 'application/json'); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers(); self.wfile.write(json.dumps(WEIGHT_CLASS_DATA).encode())
        elif self.path == '/model_weights': self.send_response(200); self.send_header('Content-type', 'application/json'); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers(); self.wfile.write(json.dumps(MODEL.get('weights', {})).encode())
        else: self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path == '/predict':
            print(f"\n--- RECEIVED POST REQUEST ---")
            content_length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(content_length))
            print(f"DEBUG: Request body: {body}")
            prediction = predict_winner(body.get('red_fighter', '').strip(), body.get('blue_fighter', '').strip())
            self.send_response(200); self.send_header('Content-type', 'application/json'); self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers(); self.wfile.write(json.dumps(prediction).encode())
        else: self.send_response(404); self.end_headers()
    def do_OPTIONS(self):
        self.send_response(200); self.send_header('Access-control-allow-origin', '*'); self.send_header('Access-control-allow-methods', 'GET, POST, OPTIONS'); self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type"); self.end_headers()

def run_server(port=8000):
    load_data()
    if not MODEL: print("Could not load model. Aborting server start."); return
    with socketserver.TCPServer(('', port), PredictionServer) as httpd: print(f"Serving at port {port}"); httpd.serve_forever()

if __name__ == "__main__":
    run_server()
