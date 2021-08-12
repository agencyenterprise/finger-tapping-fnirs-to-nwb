import json

import pandas as pd


def get_bids_version(bids_path):
    """Returns the BIDS Version of the dataset from the dataset description."""
    dataset_description = get_dataset_description(bids_path)
    return dataset_description["BIDSVersion"]


def get_dataset_authors(bids_path):
    """Returns the Authors of the dataset from the dataset description."""
    dataset_description = get_dataset_description(bids_path)
    return dataset_description["Authors"]


def get_dataset_description(bids_path):
    """Returns a dictionary with data from the dataset_description json file."""
    dataset_description_path = bids_path / "dataset_description.json"
    with open(dataset_description_path, "r") as f:
        dataset_description = json.load(f)
    return dataset_description


def get_coordinate_frame_description(bids_path, subject_id):
    """Returns a dictionary with data from the coordsystem json file."""
    subject_dir = get_subject_dir(bids_path, subject_id)
    with open(subject_dir / f"{subject_id}_coordsystem.json", "r") as f:
        return json.load(f)


def get_sidecar_metadata(bids_path, subject_id):
    """Returns a dictionary with data from the subject sidecar json file."""
    subject_dir = get_subject_dir(bids_path, subject_id)
    with open(subject_dir / f"{subject_id}_task-tapping_nirs.json", "r") as f:
        return json.load(f)


def get_subject_dir(bids_path, subject_id):
    """Returns the nirs directory corresponding to the given subject."""
    return bids_path / subject_id / "nirs"


def load_stim_table(bids_path, subject_id):
    """Returns the table of all stimulus events for the subject."""
    subject_dir = get_subject_dir(bids_path, subject_id)
    stim_path = subject_dir / f"{subject_id}_task-tapping_events.tsv"
    stim_table = pd.read_csv(stim_path, sep="\t")
    # ignore the start and end of experiment events as they are not stimulus
    stim_table = stim_table[stim_table.value != 15]
    return stim_table


def list_subject_ids(bids_path):
    """Returns a list of the ids for the subjects in the dataset."""
    participant_path = bids_path / "participants.tsv"
    participant_table = pd.read_csv(participant_path, sep="\t")
    return participant_table.participant_id.to_list()
