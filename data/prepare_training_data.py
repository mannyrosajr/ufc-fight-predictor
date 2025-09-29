import csv
import random

def get_rank(rank_str, unranked_value=20):
    if rank_str == 'C': return 0
    try: return float(rank_str)
    except (ValueError, TypeError): return unranked_value

def to_float(value, default=0.0):
    try: return float(value)
    except (ValueError, TypeError): return default

def prepare_and_engineer_data():
    with open('processed_data.csv', 'r') as infile:
        reader = csv.DictReader(infile)
        rows = [row for row in reader if row['Winner']]

    engineered_rows = []
    
    # Define all the attributes we want to find the difference for.
    # The key is the new feature name, the value is the base attribute name.
    diff_map = {
        'HeightDif': 'HeightDif', 'ReachDif': 'ReachDif', 'AgeDif': 'AgeDif',
        'LossDif': 'Losses', 'SigStrDif': 'AvgSigStrLanded', 'AvgTDDif': 'AvgTDLanded',
        'TotalRoundDif': 'TotalRoundDif', 'TotalTitleBoutDif': 'TotalTitleBoutDif',
        'WeightDif': 'WeightLbs', 'AvgSigStrPctDif': 'AvgSigStrPct', 'AvgTDPctDif': 'AvgTDPct',
        'AvgSubAttDif': 'AvgSubAtt', 'WinsDif': 'Wins', 'OddsDif': 'Odds'
    }

    for row in rows:
        try:
            new_row = {}
            new_row['Winner'] = 1 if row['Winner'] == 'Red' else 0

            # Calculate all difference features
            for key, attr in diff_map.items():
                # Handle pre-calculated diffs vs new diffs
                if 'Dif' in attr:
                    new_row[key] = to_float(row[attr])
                else:
                    new_row[key] = to_float(row[f'Red{attr}']) - to_float(row[f'Blue{attr}'])
            
            # Special case for RankDif
            new_row['RankDif'] = get_rank(row['RMatchWCRank']) - get_rank(row['BMatchWCRank'])

            engineered_rows.append(new_row)

        except (ValueError, TypeError, KeyError) as e:
            continue

    # --- Splitting and Writing Data ---
    random.shuffle(engineered_rows)
    split_index = int(len(engineered_rows) * 0.8)
    training_data = engineered_rows[:split_index]
    testing_data = engineered_rows[split_index:]
    header = list(engineered_rows[0].keys())

    for filename, data in [('training.csv', training_data), ('testing.csv', testing_data)]:
        with open(filename, 'w', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=header)
            writer.writeheader()
            writer.writerows(data)
    
    print(f"Successfully created final training.csv ({len(training_data)} rows) and testing.csv ({len(testing_data)} rows).")

if __name__ == '__main__':
    prepare_and_engineer_data()