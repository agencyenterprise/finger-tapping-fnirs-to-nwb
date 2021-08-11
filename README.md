# finger-tapping-fnirs-to-nwb

This repo contains python source code for converting data files in the [BIDS-NIRS-Tapping](https://github.com/rob-luke/BIDS-NIRS-Tapping) dataset from [SNIRF](https://github.com/fNIRS/snirf) format to [NWB](https://www.nwb.org/nwb-neurophysiology/) format using the [ndx-nirs](https://github.com/agencyenterprise/ndx-nirs) extension. The NWB files will be placed in a directory structure appropriate for upload to the [DANDI archive](https://gui.dandiarchive.org/).

**Note:** this repo is at a WIP stage. Improved organization, documentation, unit tests, etc are expected to be added with time.


## Install Dependencies

```bash
$ pip install -r requirements.txt
```

## Get Dataset

```bash
$ mkdir data
$ cd data
$ wget https://github.com/rob-luke/BIDS-NIRS-Tapping/archive/388d2cdc3ae831fc767e06d9b77298e9c5cd307b.zip -O BIDS-NIRS-Tapping.zip
$ unzip BIDS-NIRS-Tapping.zip
$ mv BIDS-NIRS-Tapping-388d2cdc3ae831fc767e06d9b77298e9c5cd307b BIDS-NIRS-Tapping
```

## Usage

```bash
$ python convert_tapping_dataset_to_nirs.py data/BIDS-NIRS-Tapping data/dandiset_staging
```

This will read in the snirf files and BIDS metadata from `data/BIDS-NIRS-Tapping`, and output the nwb files in a dandiset-appropriate filestructure inside of `data/dandiset_staging`. The input dataset path must already exist. If the output path does not exist it will be created.

For more usage information, you can execute:
```bash
$ python convert_tapping_dataset_to_nirs.py --help
```

## Data Mapping Details

The currently implemented SNIRF -> NWB mapping is as follows:

* `/formatVersion` -> `NWBFile.notes`
* `/nirs/data1/dataTimeSeries` -> `NIRSSeries.data`
* `/nirs/data1/time` -> `NIRSSeries.timestamps`
* `/nirs/data1/measurementList{i}/sourceIndex` -> `NIRSChannelsTable.source`
* `/nirs/data1/measurementList{i}/detectorIndex` -> `NIRSChannelsTable.detector`
* `/nirs/data1/measurementList{i}/wavelengthIndex` -> `NIRSChannelsTable.source_wavelength`
* `/nirs/data1/measurementList{i}/dataType` -> Checked but not mapped. Must have a value of `1` (Continuous Wave - Amplitude)
* `/nirs/data1/measurementList{i}/dataTypeIndex` -> Checked but not mapped. Must have a value of `1`
* `/nirs/metaDataTags/SubjectID` -> `Subject.subject_id`
* `/nirs/metaDataTags/DateOfBirth` -> `Subject.date_of_birth`
* `/nirs/metaDataTags/sex` -> `Subject.sex`
* `/nirs/metaDataTags/MeasurementDate` -> `NWBFile.session_start_time`
* `/nirs/metaDataTags/MeasurementTime` -> `NWBFile.session_start_time`
* `/nirs/metaDataTags/LengthUnit` ->  Checked but not mapped. Must have a value of `'m'`
* `/nirs/metaDataTags/TimeUnit` -> Checked but not mapped. Must have a value of `'s'`
* `/nirs/metaDataTags/FrequencyUnit` -> Checked but not mapped. Must have a value of `'Hz'`
* `/nirs/metaDataTags/MNE_coordFrame` -> Not Mapped
* `/nirs/probe/wavelengths` -> `NIRSChannelsTable.source_wavelength`
* `/nirs/probe/sourcePos3D` -> `NIRSSourcesTable.{x,y,z}`
* `/nirs/probe/sourceLabels` -> `NIRSSourcesTable.label`
* `/nirs/probe/detectorPos3D` -> `NIRSSourcesTable.{x,y,z}`
* `/nirs/probe/detectorLabels` -> `NIRSSourcesTable.label`
* `/nirs/probe/landmarkPos3D` -> Not Mapped
* `/nirs/probe/landmarkLabels` -> Not Mapped
* `/nirs/stim{i}/name` -> Not Mapped (equivalent info mapped from BIDS events tsv)
* `/nirs/stim{i}/data` -> Not Mapped (equivalent info mapped from BIDS events tsv)

Some additional data is mapped from BIDS metadata files:

* `dataset_description.json`:
    * `"BIDSVersion"` -> `NWBFile.notes`
    * `"Authors"` -> `NWBFile.experimenter`
* `subj-{i}/nirs/subj-{j}_coordsystem.json`
    * `"NIRSCoordinateSystem"` -> `NWBFile.notes`
    * `"NIRSCoordinateSystemDescription"` -> `NWBFile.notes`
    * `"NIRSCoordinateUnits"` -> `NWBFile.notes`
* `subj-{i}/nirs/subj-{j}_task-tapping_nirs.json`
    * `"TaskName"` -> `NWBFile.notes`
    * `"PowerLineFrequency"` -> `NWBFile.notes`
* `subj-{i}/nirs/subj-{j}_task-tapping_events.tsv` -> `TimeSeries` in `NWBFile.stimulus`


## Uploading dataset to the DANDI archive

This dataset has been posted as dandiset `DANDI:000122`:
https://gui.dandiarchive.org/#/dandiset/000122

The full instructions for uploading a dandiset can be found here: https://www.dandiarchive.org/handbook/10_using_dandi/#uploading-a-dandiset

The DANDI documentation should be used as the source of truth. Below is a summary of commands used to upload the first draft of the dandiset (using `dandi==0.26.1`).

To print out information on the dandiset:
```
$ dandi ls -r https://identifiers.org/DANDI:000122
```

To validate the nwb files for use in a dandiset:
```
$ dandi validate data/dandiset_staging
```
Everything should pass.

Next, download the dandiset. This is even required for an empty dandiset, as it will download the metadata file and setup the directory structure.
```
$ cd data
$ dandi download https://dandiarchive.org/dandiset/000122/draft
```

Now we can use dandi to automatically reorganize the nwb files in the appropriate way. First we'll do it as a dry run just to verify the process.
```
$ cd 000122
$ dandi organize ../dandiset_staging -f dry
```
Note that this will automatically rename the nwb files according to a pre-defined schema. Execute `dandi organize --help` for more information.

If everything looks good, go ahead and let the reorganization actually run
```
$ dandi organize ../dandiset_staging
```

Assuming everything looks good at this point, the dandiset is ready to upload!
```
$ dandi upload
```

Note: these steps were used to upload the first draft of the nwb files. The process for updating with new nwb files is similar. The files which are to be replaced should be manually deleted before running `dandi organize`. All other steps are the same.

### DANDI Metadata

The following metadata was entered manually on the dandiset page:
* `Dandiset title`: Human fNIRS recordings of motor cortex during finger-tapping task
* `Description`: This experiment examines how the motor cortex is activated during a finger-tapping task. Participants are asked to either tap their left thumb to fingers, tap their right thumb to fingers, or no cue is given (control). Tapping lasts for 5 seconds and is prompted by an auditory cue. Sensors are placed over the motor cortex as described in the montage section in the link below, short channels are attached to the scalp too. Further details about the experiment (including presentation code) can be found at https://github.com/rob-luke/experiment-fNIRS-tapping.
* `License`: spdx:CC-BY-4.0
* `Keywords`: fNIRS, Haemodynamics, Motor Cortex, Finger Tapping Task
* `Dandiset Contributors`: managed by `Ownership` field
* `Related Resource`: 
  * `dcite:IsOriginalFormOf`: https://github.com/rob-luke/BIDS-NIRS-Tapping
  * `dcite:IsDescribedBy`: https://github.com/rob-luke/experiment-fNIRS-tapping
