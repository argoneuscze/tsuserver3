# A small tool to help with extracting music length data.

# Input:
#   - YAML with categories and songs
#   - Folder containing songs (mp3 / opus)
#   - (Optional) Folder where to copy selected songs
# Output:
#   - YAML with categories and songs with correct timing
#   - Folder containing selected songs (if copying)

import os
import sys
from shutil import copyfile

import yaml
from tinytag import TinyTag

# Input
src_yaml = sys.argv[1]
song_folder = sys.argv[2]
copy_dir = ""
if len(sys.argv) == 4:
    copy_dir = sys.argv[3]
    try:
        os.makedirs(copy_dir)
    except OSError:
        pass

# get list of songs
song_list = dict()
for file in os.listdir(song_folder):
    filename, extension = os.path.splitext(file)
    song_list[filename] = extension[1:]

# read yaml
with open(src_yaml, "r") as yaml_file:
    yaml_data = yaml.load(yaml_file, Loader=yaml.FullLoader)

# iterate over it, updating the data
for item in yaml_data:
    for song in item["songs"]:
        name = song["name"]

        tgt_file = f"{name}.{song_list[name]}"
        tag = TinyTag.get(os.path.join(song_folder, tgt_file))
        song["length"] = tag.duration

        # copy file
        if copy_dir:
            copyfile(
                os.path.join(song_folder, tgt_file), os.path.join(copy_dir, tgt_file)
            )

# write updated yaml
with open("_output.yaml", "w") as out_yaml:
    yaml.dump(yaml_data, out_yaml, sort_keys=False)
