"""
RANDOMLY Takes 10,000 lines from ../raw_data/raw_squality_train.jsonl, 1,000 lines from ../raw_data/raw_squality_test.jsonl, and 1,000 lines from ../raw_data/raw_squality_val.jsonl. Then converts each one to simplified JSONL.

"""
import random
import json
import os

def reservoir_sample(file_path, k):
    reservoir = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i < k:
                reservoir.append(line.strip())
            else:
                j = random.randint(0, i)
                if j < k:
                    reservoir[j] = line.strip()
    return reservoir

def write_jsonl(lines, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines):
            data = json.loads(line)
            # Extract key fields from the data
            source_type = data.get("source_type", "")
            query_synthesized = data.get("query_synthesized", "")
            summary = data.get("summary", "")
            document = data.get("document", "")
            
            new_data = {
                "id": i,
                "original_source": "SQuALITY",
                "source_type": source_type,
                "query": query_synthesized,
                "summary": summary,
                "document": document[:500] if document else ""  # Truncate long documents
            }
            json.dump(new_data, f, indent=2)
            f.write('\n')

print("Cleaning SQuALITY dataset...")

ta = '../raw_data/raw_squality_train.jsonl'
tb = '../raw_data/raw_squality_test.jsonl'
vc = '../raw_data/raw_squality_val.jsonl'

train_loc = '../clean1/squality/squality_train_10k.jsonl'
test_loc = '../clean1/squality/squality_test_1k.jsonl'
val_loc = '../clean1/squality/squality_val_1k.jsonl'

print("Sampling lines from raw data files...")

train_lines = reservoir_sample(ta, 10000)
test_lines = reservoir_sample(tb, 1000)
val_lines = reservoir_sample(vc, 1000)

print("Collected Samples. Writing to JSONL files...")

write_jsonl(train_lines, train_loc)
write_jsonl(test_lines, test_loc)
write_jsonl(val_lines, val_loc)

print("Done")
