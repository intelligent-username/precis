"""
RANDOMLY Takes 10,000 lines from ../raw_data/raw_data_msmarco_train.csv, 1,000 lines from ../raw_data/raw_data_msmarco_val.csv. Then converts each one to JSONL.

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
        for i, row in enumerate(rows):
            new_data = {
                "id": i,
                "original_source": "MSMarco",
                "query": row.get("query", ""),
                "answers": row.get("answers", ""),
                "passage": row.get("finalpassage", "")
            }
            json.dump(new_data, f, indent=2)
            f.write('\n')

print("Cleaning MSMarco dataset...")

ta = '../raw_data/raw_data_msmarco_train.csv'
tb = '../raw_data/raw_data_msmarco_val.csv'

train_loc = '../clean1/msm/msmarco_train_10k.jsonl'
test_loc = '../clean1/msm/msmarco_val_1k.jsonl'

print("Sampling rows from raw data CSV files...")

train_rows = reservoir_sample_csv(ta, 10000)
test_rows = reservoir_sample_csv(tb, 1000)

print("Collected Samples. Writing to JSONL files...")

write_jsonl(train_rows, train_loc)
write_jsonl(test_rows, test_loc)

print("Done")
