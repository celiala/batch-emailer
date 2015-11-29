import os
import sys
from emailer.template import TextFormatter

KEY_PARAM = "company_name"
VALUE1 = "LEFT "
VALUE2 = "RIGHT"
FIELD_NAME = "which"

def generate_hash(filename):
    if not os.path.isfile(filename):
        print filename, "must be a valid file"
        return None
    with open(filename, 'r') as f:
        contents = f.read()
    entries = TextFormatter.get_entries(contents)
    return {e[KEY_PARAM]: e for e in entries}

if len(sys.argv) < 3:
    print "Usage: python tsv_diff.py [file1] [file2]"
    exit(1)

file1 = sys.argv[1]
file2 = sys.argv[2]

hash1 = generate_hash(file1)
hash2 = generate_hash(file2)

if not hash1 or not hash2:
    exit(1)

hash_diff = {}
fields = []

for hash_key in hash1:
    value1 = {}
    value2 = {}
    entry1 = hash1[hash_key]
    if hash_key not in hash2:
        value1[KEY_PARAM] = hash_key
        value2[KEY_PARAM] = None
        if KEY_PARAM not in fields:
            fields.append(KEY_PARAM)
    else:
        entry2 = hash2[hash_key]
        for entry_key in entry1:
            if entry_key not in entry2:
                if entry1[entry_key]:
                    value1[entry_key] = entry1[entry_key]
                    value2[entry_key] = None
                    if entry_key not in fields:
                        fields.append(entry_key)
            elif entry1[entry_key] != entry2[entry_key]:
                value1[entry_key] = entry1[entry_key]
                value2[entry_key] = entry2[entry_key]
                if entry_key not in fields:
                    fields.append(entry_key)
    if value1.keys():
        hash_diff[hash_key] = {
            VALUE1: value1,
            VALUE2: value2
        }
for hash_key in hash2:
    value1 = {}
    value2 = {}
    entry2 = hash2[hash_key]
    if hash_key not in hash1:
        value1[KEY_PARAM] = None
        value2[KEY_PARAM] = hash_key
        if KEY_PARAM not in fields:
            fields.append(KEY_PARAM)
    if value1.keys():
        hash_diff[hash_key] = {
            VALUE1: value1,
            VALUE2: value2
        }

# print headers
print "%s\t%s\t%s" % (FIELD_NAME, "key", "\t".join(fields))

for v in [VALUE1, VALUE2]:
    for hash_key in hash_diff:
        field_values = []
        for f in fields:
            hash_values = hash_diff[hash_key][v]
            if f in hash_values and hash_values[f]:
                field_values.append(hash_values[f])
            else:
                field_values.append('')
        print "%s\t%s\t%s" % (v, hash_key, "\t".join(field_values))
