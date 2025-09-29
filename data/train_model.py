import csv
import json
import math

def calculate_scaling_params(data, features):
    params = {}
    for feature in features:
        try:
            values = [float(row[feature]) for row in data if row[feature]]
            if not values:
                continue
            mean = sum(values) / len(values)
            std_dev = math.sqrt(sum([(v - mean) ** 2 for v in values]) / len(values))
            if std_dev == 0:
                std_dev = 1
            params[feature] = {'mean': mean, 'std_dev': std_dev}
        except (ValueError, TypeError):
            continue
    return params

def train_model(learning_rate=0.01, iterations=1000):
    with open('training.csv', 'r') as infile:
        reader = csv.DictReader(infile)
        data = list(reader)
        if not data:
            print("Training data is empty.")
            return

    features = [h for h in data[0].keys() if h != 'Winner']
    
    scaling_params = calculate_scaling_params(data, features)

    weights = {feature: 0.0 for feature in features}
    bias = 0.0

    for i in range(iterations):
        d_weights = {feature: 0.0 for feature in features}
        d_bias = 0.0
        
        for row in data:
            z = bias
            for feature in features:
                if feature in scaling_params and row[feature]:
                    try:
                        scaled_value = (float(row[feature]) - scaling_params[feature]['mean']) / scaling_params[feature]['std_dev']
                        z += weights[feature] * scaled_value
                    except (ValueError, TypeError):
                        continue

            z = max(-100, min(100, z)) # Clipping z to prevent overflow
            prediction = 1 / (1 + math.exp(-z))
            
            error = prediction - float(row['Winner'])
            
            d_bias += error
            for feature in features:
                if feature in scaling_params and row[feature]:
                    try:
                        scaled_value = (float(row[feature]) - scaling_params[feature]['mean']) / scaling_params[feature]['std_dev']
                        d_weights[feature] += error * scaled_value
                    except (ValueError, TypeError):
                        continue

        num_samples = len(data)
        bias -= learning_rate * (d_bias / num_samples)
        for feature in features:
            if feature in d_weights:
                weights[feature] -= learning_rate * (d_weights[feature] / num_samples)

    model = {'weights': weights, 'bias': bias, 'scaling_params': scaling_params}
    with open('model.json', 'w') as outfile:
        json.dump(model, outfile, indent=4)

    print("Model training complete. Model saved to model.json")

if __name__ == '__main__':
    train_model()