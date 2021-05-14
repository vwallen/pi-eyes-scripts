# pi-eyes-scripts

Scripts in this repo:

- `auto-capture.py` Captures images at regular intervals into the specified directory.
  Use `auto-capture.py --help` to for usage information
- `capture-interest.py` Captures images at regular intervals based on a model trained with *interesting* and *uninteresting* labels. 
  Usage `capture-interest.py /path/to/save/images /path/of/model/directory`
  Takes optional `--check` and `--interval` arguments to set seconds between checks for *interesting* images and seconds between capturing *intresting* images.
- `cat-detection.py` Captures images into directories based on labels in a categories model, if they are *interesting*.
  Usage `cat-detection.py /path/to/save/images /path/of/interest/model/directory /path/of/category/model/directory`
  Takes optional `--check` and `--interval` arguments to set seconds between checks for *interesting* images and seconds between capturing *intresting* images.
