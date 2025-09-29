
import csv

# Column names to extract
feature_names = [
    'Winner', 'HeightDif', 'ReachDif', 'AgeDif', 'WinStreakDif', 'LossDif',
    'SigStrDif', 'AvgTDDif', 'BlueAvgSigStrLanded', 'RedAvgSigStrLanded',
    'BlueAvgSigStrPct', 'RedAvgSigStrPct', 'BlueAvgTDLanded', 'RedAvgTDLanded',
    'BlueAvgTDPct', 'RedAvgTDPct', 'BlueAvgSubAtt', 'RedAvgSubAtt',
    'TotalRoundDif', 'TotalTitleBoutDif', 'BlueWins', 'RedWins', 'BlueLosses',
    'RedLosses', 'RedStance', 'BlueStance', 'RedOdds', 'BlueOdds',
    'RedWeightLbs', 'BlueWeightLbs',
    'RMatchWCRank', 'BMatchWCRank'
]

with open('ufc-master.csv', 'r') as infile, open('processed_data.csv', 'w', newline='') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.DictWriter(outfile, fieldnames=feature_names)

    writer.writeheader()

    for row in reader:
        try:
            selected_row = {key: row[key] for key in feature_names}
            writer.writerow(selected_row)
        except KeyError as e:
            print(f"Skipping row due to missing key: {e}")
            print(f"Row content: {row}")

