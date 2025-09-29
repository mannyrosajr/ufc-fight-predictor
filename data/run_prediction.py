from api_server import load_data, predict_winner
import json

# Load the model and all fighter data
load_data()

# Define the matchup
red_fighter = "Michinori Tanaka"
blue_fighter = "Merab Dvalishvili"

# Get the prediction
prediction = predict_winner(red_fighter, blue_fighter)

# Print the results in a readable format
print(f"--- Prediction Analysis: {red_fighter} vs. {blue_fighter} ---")
if prediction.get('error'):
    print(f"An error occurred: {prediction['error']}")
else:
    print(f"Predicted Winner: {prediction['PredictedWinner']}")
    print(f"Confidence: {prediction['Confidence']}")
    print("\n--- Expert Analysis ---")
    if prediction.get('explanation'):
        print(f"Main Factor: {prediction['explanation']['main_point']}")
        print("\nSupporting Details:")
        for detail in prediction['explanation']['details']:
            print(f"- {detail}")
    else:
        print("No detailed explanation was generated.")

