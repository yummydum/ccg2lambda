import csv
from pathlib import Path


def main():
    """
    Create available axiom for each pair
    """
    result_path = Path('data/annotation_data.tsv')
    with result_path.open(mode='r') as f:
        data = csv.reader(f, delimiter='\t', lineterminator='\n')
        next(data)
        for line in data:
            breakpoint()
    return


if __name__ == "__main__":
    main()