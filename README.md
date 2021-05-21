# finger-tapping-fnirs-to-nwb

This repo contains python source code for converting data files in the [BIDS-NIRS-Tapping](https://github.com/rob-luke/BIDS-NIRS-Tapping) dataset from [SNIRF](https://github.com/fNIRS/snirf) format to [NWB](https://www.nwb.org/nwb-neurophysiology/) format using the [ndx-nirs](https://github.com/agencyenterprise/ndx-nirs) extension. In addition, scripts for arranging the files and uploading to the [DANDI archive](https://gui.dandiarchive.org/) are included.

**Note:** this repo is at a very early WIP stage. Proper organization, documentation, unit tests, etc will be added with time.


## Installation

Note: eventually this will be converted over to install via setup.py or poetry

```bash
$ pip install -r requirements.txt
```


## Get Dataset

```bash
$ mkdir data
$ cd data
$ git clone https://github.com/rob-luke/BIDS-NIRS-Tapping.git
```

## Usage

```bash
$ python convert_tapping_dataset_to_nirs.py
```


## Example

WIP
