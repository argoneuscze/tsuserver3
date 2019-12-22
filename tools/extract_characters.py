# A small script that extracts the characters folder into a character YAML file.

import os
import sys

import yaml

char_folder = sys.argv[1]
target_file = sys.argv[2]

char_list = []
for path in os.listdir(char_folder):
    if os.path.isdir(path):
        char_list.append(path)

with open(target_file, "w") as out_yaml:
    yaml.dump(char_list, out_yaml, sort_keys=False)
