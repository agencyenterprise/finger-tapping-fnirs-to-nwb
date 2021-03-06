import os
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
    get_subject_dir,
    list_subject_ids,
    load_stim_table,
)
from nwb import convert_to_nwb
from snirf import get_format_version, load_snirf

CONVERTER_VERSION = "0.1.0"

# copied (with minimal edits) from:
# https://github.com/rob-luke/BIDS-NIRS-Tapping/blob/388d2cdc3ae831fc767e06d9b77298e9c5cd307b/README.md
EXPERIMENT_DESCRIPTION = """This experiment examines how the motor cortex is activated
during a finger-tapping task. Participants are asked to either tap their left thumb to
fingers, tap their right thumb to fingers, or no cue is given (control). Tapping lasts
for 5 seconds and is prompted by an auditory cue. Sensors are placed over the motor
cortex as described in the montage section in the link below, short channels are
attached to the scalp too. Further details about the experiment (including presentation
code) can be found at https://github.com/rob-luke/experiment-fNIRS-tapping.
"""
INSTITUTION = "Macquarie University"
PUBLICATIONS = ""
KEYWORDS = ["fNIRS", "Haemodynamics", "Motor Cortex", "Finger Tapping Task"]


@click.command()
@click.argument(
    "dataset_path", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.argument("output_path", type=click.Path(file_okay=False, path_type=Path))
def main(dataset_path, output_path):
    """Convert the fNIRS finger-tapping dataset to NWB for upload to the DANDI Archive.

    This script is built to work specifically with the following dataset:
    https://github.com/rob-luke/BIDS-NIRS-Tapping
    (most recently updated to work with dataset commit 388d2cdc)

    \b
    DATASET_PATH is the path to the root directory of the dataset.
    OUTPUT_PATH is the path where the root of the output dataset should go.

    The script maps SNIRF fields to NWB fields and outputs a .nwb file for each .snirf
    file. Additionally, certain BIDS metadata which is not available in the snirf files
    has been incorporated in to the NWB files.

    If OUTPUT_PATH does not exist, it will be created.
    """
    print("converting all snirf files in the input dataset to nwb...")
    print(f"dataset directory: {dataset_path}")
    print(f"output directory: {output_path}")
    print()

    for subject_id in list_subject_ids(dataset_path):
        convert_subject_snirf_to_nwb(
            input_root=dataset_path, output_root=output_path, subject_id=subject_id
        )

    print()
    print("Conversion successful!")


def convert_subject_snirf_to_nwb(*, input_root, output_root, subject_id):
    """Converts the snirf file into an nwb file for a particular subject.

    The nwb file written to disk has the same filename stem as the snirf file.

    Args:
        input_root (pathlib.Path): the root of the input dataset. Must exist.
        output_root (pathlib.Path): the root of the output dataset. Will be created if
            it does not exist.
        subject_id (str): a string id in the form of 'sub-{02d}'. Must match an
            existing subject in the input dataset.
    """

    snirf_path = _get_subject_input_path(input_root, subject_id)
    nwb_path = _prepare_subject_output_path(output_root, subject_id)
    print("converting SNIRF --> NWB:")
    print(f"  {snirf_path} --> {nwb_path}")

    snirf_data = load_snirf(snirf_path)
    nwb = convert_to_nwb(
        snirf_data,
        file_identifier=snirf_path.stem,
        session_description=(
            f"fNIRS recording data for a finger-tapping task for subject {subject_id}"
        ),
        manufacturer="SNIRF",
        nirs_mode="continuous-wave",
        stimulus_data=load_stim_table(input_root, subject_id),
        notes=_compile_dataset_specific_notes(
            snirf=snirf_data, dataset_path=input_root, subject_id=subject_id
        ),
        experimenter=get_dataset_authors(input_root),
        experiment_description=EXPERIMENT_DESCRIPTION,
        institution=INSTITUTION,
        keywords=KEYWORDS,
        publications=PUBLICATIONS,
    )

    with NWBHDF5IO(str(nwb_path), "w") as io:
        io.write(nwb)


def _get_subject_input_path(input_root, subject_id):
    """Builds the path to an existing subject .snirf file."""
    subject_dir = get_subject_dir(input_root, subject_id)
    return subject_dir / f"{subject_id}_task-tapping_nirs.snirf"


def _prepare_subject_output_path(output_root, subject_id):
    """Builds the path to the desired output .nwb file.

    Creates parent directories if needed.
    """
    output_dir = output_root / subject_id
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / f"{subject_id}_task-tapping_nirs.nwb"


def _compile_dataset_specific_notes(*, snirf, dataset_path, subject_id):
    """Compile a variety of miscellaneous information for use in the notes field."""

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
    return _serialize_notes(notes)


def _serialize_notes(notes):
    """Compile the notes dictionary into a string format.

    Returns a multi-line string where each line corresponds to a key-value pair in the
    format: '{key}: {value}'
    """
    note_lines = [f"{key}: {value}" for key, value in notes.items()]
    return "\n".join(note_lines)


if __name__ == "__main__":
    main()
