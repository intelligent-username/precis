"""
RANDOMLY Takes 10,000 lines from ../raw_data/raw_dialogsum_train.csv, 1,000 lines from ../raw_data/raw_dialogsum_test.csv, and 700 lines from ../raw_data/raw_dialogsum_val.csv. Then converts each one to JSONL.

"""
import random
import json
import csv
import os

def reservoir_sample_csv(file_path, k):
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    if len(rows) <= k:
        return rows
    return random.sample(rows, k)

def write_jsonl(rows, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for row in rows:
            new_data = {
                "id": row["id"],
                "original_source": "DialogSum",
                "dialogue": row["dialogue"],
                "summary": row["summary"],
                "topic": row["topic"]
            }
            json.dump(new_data, f, indent=2)
            f.write('\n')

print("Cleaning DialogSum dataset...")

ta = '../raw_data/raw_dialogsum_train.csv'
tb = '../raw_data/raw_dialogsum_test.csv'
vc = '../raw_data/raw_dialogsum_val.csv'

train_loc = '../clean1/ds/dialogsum_train_10k.jsonl'
test_loc = '../clean1/ds/dialogsum_test_1k.jsonl'
val_loc = '../clean1/ds/dialogsum_val_700.jsonl'

print("Sampling rows from raw data CSV files...")

train_rows = reservoir_sample_csv(ta, 10000)
test_rows = reservoir_sample_csv(tb, 1000)
val_rows = reservoir_sample_csv(vc, 700)

print("Collected Samples. Writing to JSONL files...")

write_jsonl(train_rows, train_loc)
write_jsonl(test_rows, test_loc)
write_jsonl(val_rows, val_loc)

print("Done")