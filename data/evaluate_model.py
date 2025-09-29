
import csv
import json
import math

def evaluate_model():
    # Load the model
    try:
        with open('model.json', 'r') as infile:
            model = json.load(infile)
    except FileNotFoundError:
        print("Error: model.json not found. Please train the model first.")
        return
    
    weights = model['weights']
    bias = model['bias']
    scaling_params = model['scaling_params']

    # Read testing data
    try:
        with open('testing.csv', 'r') as infile:
            reader = csv.DictReader(infile)
            data = list(reader)
            if not data:
                print("Testing data is empty.")
                return
    except FileNotFoundError:
        print("Error: testing.csv not found.")
        return

    features = [h for h in data[0].keys() if h != 'Winner']
    
    correct_predictions = 0
    total_predictions = len(data)

    for row in data:
        z = bias
        for feature in features:
            if feature in scaling_params and row.get(feature):
                try:
                    scaled_value = (float(row[feature]) - scaling_params[feature]['mean']) / scaling_params[feature]['std_dev']
                    z += weights[feature] * scaled_value
                except (ValueError, TypeError, KeyError):
                    # This can happen if a feature in the test set wasn't in the training set (e.g., a new stance)
                    continue
        
        z = max(-100, min(100, z))
        prediction_prob = 1 / (1 + math.exp(-z))
        
        prediction = 1 if prediction_prob >= 0.5 else 0
        
        try:
            actual = int(row['Winner'])
            if prediction == actual:
                correct_predictions += 1
        except (ValueError, TypeError):
            print(f"Warning: Could not convert Winner ' {row['Winner']} ' to int.")
            total_predictions -= 1 # Don't count this row in accuracy calculation

    accuracy = (correct_predictions / total_predictions) * 100 if total_predictions > 0 else 0
    
    print(f"Model Accuracy on the test set: {accuracy:.2f}%")

if __name__ == '__main__':
    evaluate_model()
