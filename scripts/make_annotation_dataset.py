import csv
from pathlib import Path
import json


def main():
    data_dir = Path('data/created_axioms')
    result_path = Path('data/annotation_data.csv')
    with result_path.open(mode='w') as f:
        writer = csv.writer(f, quotechar='"', lineterminator='\n')
        writer.writerow(["situation", "subgoal"])
        for p in data_dir.iterdir():
            with p.open(mode='r') as f:
                data = json.load(f)
            if data['readable_subgoals']:
                for r_goal in set(data['readable_subgoals']):
                    writer.writerow([data['premise'], r_goal])
    return


if __name__ == "__main__":
    main()