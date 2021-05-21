import sys
import re
from pathlib import Path

from pynwb import NWBHDF5IO

# todo compile conversion tools into an installable package
sys.path.append("src")
from snirf import load_snirf
from nwb import convert_to_nwb


def list_subj_dirs(dataset_dir):
    subj_re = re.compile(r"^sub\-\d{2}$")

    def is_subj_dir(path):
        return path.is_dir() and subj_re.match(path.name)

    subj_dirs = [path for path in dataset_dir.iterdir() if is_subj_dir(path)]
    return sorted(subj_dirs)


def convert_subject_snirf_to_nwb(subj_dir):
    subj_id = subj_dir.name
    snirf_path = subj_dir / "nirs" / f"{subj_id}_task-tapping_nirs.snirf"
    nwb_path = subj_dir / "nirs" / f"{snirf_path.stem}.nwb"

    print("converting SNIRF --> NWB:")
    print(f"  {snirf_path} --> {nwb_path}")

    nwb = convert_to_nwb(
        load_snirf(snirf_path),
        file_identifier=snirf_path.stem,
        session_description=f"{subj_id} NIRS recording data for a finger-tapping task",
        manufacturer="SNIRF",
        nirs_mode="continuous-wave",
    )

    with NWBHDF5IO(str(nwb_path), "w") as io:
        io.write(nwb)


DATASET_DIR = Path("data/BIDS-NIRS-Tapping/")


# todo use click and add command line arguments and help
if __name__ == "__main__":
    print("converting all snirf files in the dataset to nwb")
    print(f"dataset directory: {DATASET_DIR}")
    for subj_dir in list_subj_dirs(DATASET_DIR):
        convert_subject_snirf_to_nwb(subj_dir)
