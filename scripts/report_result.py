from pathlib import Path
import pickle
import pandas as pd
import csv


def calc_metric(labels, pred, limit='2793'):
    fails = 0
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    p = 0
    n = 0
    p_hat = 0
    n_hat = 0
    for k, v in labels.items():

        if str(k) > limit:
            continue

        if k not in pred:
            pred[k] = 0
            fails += 1

        if labels[k] in {'ENTAILMENT', 'CONTRADICTION'}:
            p += 1
            if pred[k] == 1:
                tp += 1
                p_hat += 1
            else:
                tn += 1
                n_hat += 1
        else:
            n += 1
            if pred[k] == 1:
                fp += 1
                p_hat += 1
            else:
                fn += 1
                n_hat += 1

    precision = tp / p_hat
    recall = tp / p
    acc = (fn + tp) / (p + n)
    print('N: ', p + n)
    print('E or C', p)
    print('Neutral', n)
    print('Precision', precision)
    print('Recall', recall)
    print('Accuracy', acc)
    return precision, recall, acc


def apply_annotation(pred, annotation):
    success = []
    expected_label = dict()
    expected_label_path = Path('data/expected_label_fixed.csv')
    with expected_label_path.open(mode='r') as f:
        reader = csv.reader(f)
        for line in reader:
            if line[0].endswith('.sem.xml'):
                i = line[0].lstrip('pair_').rstrip('.sem.xml')
            else:
                expected_label[i] = line[0]
                b1 = i in annotation and annotation[i] == line[0]
                b2 = '0' not in line[0]
                if b1 and b2:
                    pred[int(i)] = 1
                    success.append(int(i))
    return pred, success


def load_labels():
    data = pd.read_csv('data/SICK_test.txt', sep="\t")
    labels = data.set_index("pair_ID")["entailment_judgment"].to_dict()
    return labels


def load_pred():
    pred_path = Path('data/pred.pkl')
    with pred_path.open(mode='rb') as f:
        pred = pickle.load(f)
    return pred


def load_pred_abd():
    pred_path = Path('data/pred_test_abd.pkl')
    with pred_path.open(mode='rb') as f:
        pred = pickle.load(f)
    return pred


def load_annotation():
    annotation = dict()
    annotated_path = Path('data/annotated.csv')
    with annotated_path.open(mode='r') as f:
        reader = csv.reader(f)
        for line in reader:
            if line[0].endswith('.sem.xml'):
                i = line[0].lstrip('pair_').rstrip('.sem.xml')
                if i <= '2727':
                    annotation[i] = line[-3].replace(' ', '')
                else:
                    annotation[i] = line[-2].replace(' ', '')
    print('Num annotated: ', len(annotation))
    return annotation


if __name__ == "__main__":
    print('Vanila ccg2lambda')
    labels = load_labels()
    pred = load_pred()
    annotation = load_annotation()
    calc_metric(labels, pred)

    print('abduction ccg2lambda')
    abd_pred = load_pred_abd()
    calc_metric(labels, abd_pred)

    print('proposed method')
    new_pred, success = apply_annotation(pred, annotation)
    calc_metric(labels, new_pred)

    print('proposed + abduction')
    for k, v in abd_pred.items():
        if k in new_pred and v == 0 and new_pred[k] == 1:
            abd_pred[k] = 1
    calc_metric(labels, abd_pred)

    # len of success annotation
    success_len = dict()
    for i in success:
        l = len(annotation[str(i)])
        if l not in success_len:
            success_len[l] = 0
        success_len[l] += 1

    n = len(success_len)
    for k, v in success_len.items():
        print('subgoal_len:', k)
        print('num:', v)

    # for k, v in abd_pred.items():
    #     if v == 1 and new_pred[k] == 0 and k >= 2727:
    #         breakpoint()