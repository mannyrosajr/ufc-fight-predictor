
import csv
import json
import math

def predict_upcoming():
    try:
        with open('model.json', 'r') as infile:
            model = json.load(infile)
    except FileNotFoundError:
        print("Error: model.json not found. Please train the model first.")
        return

    weights = model['weights']
    bias = model['bias']
    scaling_params = model['scaling_params']
    trained_features = list(weights.keys())

    try:
        with open('upcoming.csv', 'r') as infile:
            reader = csv.DictReader(infile)
            upcoming_fights = list(reader)
    except FileNotFoundError:
        print("Error: upcoming.csv not found.")
        return

    predictions = []

    for fight in upcoming_fights:
        z = bias
        # Use the same features as the model was trained on
        for feature in trained_features:
            # Handle one-hot encoded stances
            if feature.startswith('RedStance_'):
                stance = feature.replace('RedStance_', '')
                value = 1 if fight.get('RedStance') == stance else 0
                z += weights[feature] * value
                continue
            if feature.startswith('BlueStance_'):
                stance = feature.replace('BlueStance_', '')
                value = 1 if fight.get('BlueStance') == stance else 0
                z += weights[feature] * value
                continue

            # Handle numerical features
            if feature in scaling_params and fight.get(feature):
                try:
                    scaled_value = (float(fight[feature]) - scaling_params[feature]['mean']) / scaling_params[feature]['std_dev']
                    z += weights[feature] * scaled_value
                except (ValueError, TypeError, KeyError):
                    continue
        
        z = max(-100, min(100, z))
        prediction_prob = 1 / (1 + math.exp(-z)) # Probability of Red winning
        
        predicted_winner_label = 'Red' if prediction_prob >= 0.5 else 'Blue'
        winner_name = fight['RedFighter'] if predicted_winner_label == 'Red' else fight['BlueFighter']
        confidence = prediction_prob if predicted_winner_label == 'Red' else 1 - prediction_prob

        predictions.append({
            'RedFighter': fight['RedFighter'],
            'BlueFighter': fight['BlueFighter'],
            'PredictedWinner': winner_name,
            'Confidence': f"{confidence * 100:.2f}%"
        })

    with open('predictions.json', 'w') as outfile:
        json.dump(predictions, outfile, indent=4)

    print("Predictions for upcoming fights saved to predictions.json")

if __name__ == '__main__':
    predict_upcoming()
