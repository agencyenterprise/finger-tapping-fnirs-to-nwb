import json

import pandas as pd


def load_stim_table(stim_path):
    stim_table = pd.read_csv(stim_path, sep="\t")
    # ignore the start and end of experiment events as they are not stimulus
    stim_table = stim_table[stim_table.value != 15]
    return stim_table


def get_bids_version(bids_path):
    dataset_description = get_dataset_description(bids_path)
    return dataset_description["BIDSVersion"]


def get_dataset_description(bids_path):
    dataset_description_path = bids_path / 'dataset_description.json'
    with open(dataset_description_path, 'r') as f:
        dataset_description = json.load(f)
    return dataset_description


def get_coordinate_frame_description(bids_path, subject_id):
    subject_dir = bids_path / subject_id / 'nirs'
    with open(subject_dir / f'{subject_id}_coordsystem.json', 'r') as f:
        return json.load(f)


def get_sidecar_metadata(bids_path, subject_id):
    subject_dir = bids_path / subject_id / 'nirs'
    with open(subject_dir / f'{subject_id}_task-tapping_nirs.json', 'r') as f:
        return json.load(f)

def get_dataset_authors(bids_path):
    dataset_description = get_dataset_description(bids_path)
    return dataset_description["Authors"]
