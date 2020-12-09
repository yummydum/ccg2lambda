import csv
from pathlib import Path
import json


def main():
    data_dir = Path('data/created_axioms')
    result_path = Path('data/annotation_data.tsv')
    with result_path.open(mode='w') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(['sentence', 'neutral', 'entailment', 'contradiction'])
        for p in data_dir.iterdir():
            with p.open(mode='r') as f:
                data = json.load(f)
            if data['readable_subgoals']:
                writer.writerow([data['pair_id']])
                premise = f"Premise: {' '.join(data['premise'])}"
                writer.writerow([premise])
                hypothesis = f"Conclusion: {' '.join(data['conclusion'])}"
                writer.writerow([hypothesis])
                writer.writerow(["Subgoals:"])
                for r_goal in data['readable_subgoals']:
                    writer.writerow([r_goal])
                writer.writerow([])
    return


if __name__ == "__main__":
    main()