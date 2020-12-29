import pickle
import csv
from pathlib import Path
import json


def main():
    filler = "------"
    data_dir = Path('data/created_axioms')
    result_path = Path('data/annotation_data.tsv')
    with result_path.open(mode='w') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(["category", 'sentence', "label"])
        for p in data_dir.iterdir():
            with p.open(mode='r') as f:
                data = json.load(f)
            if data['readable_subgoals']:
                writer.writerow([data['pair_id'], filler, filler])
                writer.writerow(["Situation", data['premise'], filler])
                # writer.writerow(["Conslusion", data['conclusion']])
                for r_goal in data['readable_subgoals']:
                    writer.writerow(["Is it true that: ", r_goal])
                writer.writerow([filler, filler, filler, filler])
    return


if __name__ == "__main__":
    main()