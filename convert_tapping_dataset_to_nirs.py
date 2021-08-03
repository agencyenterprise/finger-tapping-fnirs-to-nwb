import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

import click
from pynwb import NWBHDF5IO

# Ensure modules in `src` are findable before importing
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from bids import (
    get_bids_version,
    get_coordinate_frame_description,
    get_dataset_authors,
    get_sidecar_metadata,
    load_stim_table,
)
from nwb import convert_to_nwb
from snirf import get_format_version, load_snirf

CONVERTER_VERSION = "0.1.0-dev.001"

# copied from: https://github.com/rob-luke/BIDS-NIRS-Tapping/blob/master/README.md
EXPERIMENT_DESCRIPTION = """This experiment examines how the motor cortex is activated
during a finger tapping task. Participants are asked to either tap their left thumb to
fingers, tap their right thumb to fingers, or nothing (control). Tapping lasts for 5
seconds as is propted by an auditory cue. Sensors are placed over the motor cortex as
described in the montage section in the link below, short channels are attached to the
scalp too. Further details about the experiment (including presentation code) can be
found at https://github.com/rob-luke/experiment-fNIRS-tapping.
"""
INSTITUTION = "Macquarie University"
PUBLICATIONS = ""
KEYWORDS = ["fNIRS", "Haemodynamics", "Motor Cortex", "Finger Tapping Task"]


def list_subj_dirs(dataset_dir):
    subj_re = re.compile(r"^sub\-\d{2}$")

    def is_subj_dir(path):
        return path.is_dir() and subj_re.match(path.name)

    subj_dirs = [path for path in dataset_dir.iterdir() if is_subj_dir(path)]
    return sorted(subj_dirs)


def convert_subject_snirf_to_nwb(dataset_path, subj_dir):
    subj_id = subj_dir.name
    snirf_path = subj_dir / "nirs" / f"{subj_id}_task-tapping_nirs.snirf"
    stim_path = subj_dir / "nirs" / f"{subj_id}_task-tapping_events.tsv"
    nwb_path = subj_dir / "nirs" / f"{snirf_path.stem}.nwb"

    print("converting SNIRF --> NWB:")
    print(f"  {snirf_path} --> {nwb_path}")

    stim_table = load_stim_table(stim_path)

    snirf_data = load_snirf(snirf_path)

    notes = compile_dataset_specific_notes(snirf_data, dataset_path, subj_id)

    nwb = convert_to_nwb(
        snirf_data,
        file_identifier=snirf_path.stem,
        session_description=f"{subj_id} NIRS recording data for a finger-tapping task",
        manufacturer="SNIRF",
        nirs_mode="continuous-wave",
        stim_data=stim_table,
        notes=notes,
        experimenter=get_dataset_authors(dataset_path),
        experiment_description=EXPERIMENT_DESCRIPTION,
        institution=INSTITUTION,
        keywords=KEYWORDS,
        publications=PUBLICATIONS,
    )

    with NWBHDF5IO(str(nwb_path), "w") as io:
        io.write(nwb)


def compile_dataset_specific_notes(snirf, dataset_path, subject_id):
    notes = OrderedDict()
    notes["Source file SNIRF version"] = get_format_version(snirf)
    notes["Source dataset BIDS version"] = get_bids_version(dataset_path)
    notes["Conversion script"] = os.path.basename(__file__)
    notes["Conversion codebase version"] = CONVERTER_VERSION

    coord_description = get_coordinate_frame_description(dataset_path, subject_id)
    desired_fields = [
        "NIRSCoordinateSystem",
        "NIRSCoordinateSystemDescription",
        "NIRSCoordinateUnits",
    ]
    for field in desired_fields:
        notes[field] = coord_description[field]

    sidecare_metadata = get_sidecar_metadata(dataset_path, subject_id)
    desired_fields = ["TaskName", "PowerLineFrequency"]
    for field in desired_fields:
        notes[field] = sidecare_metadata[field]

    return "\n".join(f"{k}: {v}" for k, v in notes.items())


@click.command()
@click.argument(
    "dataset_path", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
def main(dataset_path):
    """Convert the fNIRS finger-tapping dataset to NWB for upload to the DANDI Archive.

    This script is built to work specifically with the following dataset:
    https://github.com/rob-luke/BIDS-NIRS-Tapping
    (most recently updated to work with dataset commit 388d2cdc)

    DATASET_PATH is the path to the root directory of the dataset.

    The script maps SNIRF fields to NWB fields and outputs a .nwb file for each .snirf
    file. Additionally, certain BIDS metadata which is not available in the snirf files
    has been incorporated in to the NWB files.
    """
    print("converting all snirf files in the dataset to nwb")
    print(f"dataset directory: {dataset_path}")
    for subj_dir in list_subj_dirs(dataset_path):
        convert_subject_snirf_to_nwb(dataset_path, subj_dir)


if __name__ == "__main__":
    main()
