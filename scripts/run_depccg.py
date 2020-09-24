from pathlib import Path
import csv
from depccg.parser import EnglishCCGParser
from depccg.printer import print_
from depccg.download import load_model_directory, SEMANTIC_TEMPLATES
from depccg.tokens import annotate_using_spacy

from config import DATA_DIR


def load_sick():
    data = []
    data_path = DATA_DIR / 'SICK_train.txt'
    with data_path.open() as f:
        reader = csv.reader(f, delimiter='\t')
        col = next(reader)
        for line in reader:
            data.append(line)
    return data


def load_parser():
    kwargs = dict(binary_rules=None,
                  unary_penalty=0.1,
                  beta=0.00001,
                  use_beta=True,
                  use_category_dict=True,
                  use_seen_rules=True,
                  pruning_size=50,
                  nbest=1,
                  possible_root_cats=None,
                  max_length=250,
                  max_steps=100000,
                  gpu=-1)
    model, config = load_model_directory('en[elmo]')
    parser = EnglishCCGParser.from_json(config, model, **kwargs)
    return parser


def tokenize(doc):
    tagged_doc, doc = annotate_using_spacy([[word for word in sent.split(' ')]
                                            for sent in doc],
                                           tokenize=True,
                                           n_threads=20)
    return tagged_doc, doc


def to_xml(res, tagged_doc, result_file):
    semantic_templates = SEMANTIC_TEMPLATES.get('en')
    with result_file.open('w') as f:
        print_(res,
               tagged_doc,
               format='jigg_xml_ccg2lambda',
               lang='en',
               semantic_templates=semantic_templates,
               file=f)


def main():
    data = load_sick()
    parser = load_parser()
    for pair in data:
        tagged_doc, doc = tokenize(pair[1:3])
        res = parser.parse_doc(doc, probs=None, tag_list=None, batchsize=32)
        sick_dir = DATA_DIR / 'SICK'
        if not sick_dir.exists():
            sick_dir.mkdir()
        result_file = sick_dir / f'pair_{pair[0]}.sem.xml'
        to_xml(res, tagged_doc, result_file)


if __name__ == "__main__":
    main()