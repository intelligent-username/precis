"""
RANDOMLY Takes 10,000 lines from ../raw_data/raw_mediasum_train_data.txt, 1,000 lines from ../raw_data/raw_mediasum_test_data.txt, and 1,000 lines from ../raw_data/raw_mediasum_val_data.txt. Then converts each one to JSONL.

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
        for line in lines:
            data = json.loads(line)
            new_data = {
                "id": data["id"],
                "original_source": "MediaSum",
                "url": data["url"],
                "summary": data["summary"],
                "transcript": data["utt"],
                "speaker": data["speaker"]
            }
            json.dump(new_data, f, indent=2)
            f.write('\n')

print("Cleaning Mediasum dataset...")

ta = '../raw_data/raw_mediasum_train_data.txt'
tb = '../raw_data/raw_mediasum_test_data.txt'
vc = '../raw_data/raw_mediasum_val_data.txt'

train_loc = '../clean1/ms/mediasum_train_10k.jsonl'
test_loc = '../clean1/ms/mediasum_test_1k.jsonl'
val_loc = '../clean1/ms/mediasum_val_1k.jsonl'

print("Sampling lines from raw data files...")

train_lines = reservoir_sample(ta, 10000)
test_lines = reservoir_sample(tb, 1000)
val_lines = reservoir_sample(vc, 1000)

print("Collected Samples. Writing to JSONL files...")

write_jsonl(train_lines, train_loc)
write_jsonl(test_lines, test_loc)
write_jsonl(val_lines, val_loc)

print("Done")
