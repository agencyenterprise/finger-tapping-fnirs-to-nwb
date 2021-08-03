from datetime import datetime

import h5py
import pytz


def load_snirf(file_path):
    """Loads a snirf file and returns it as an h5py File."""
    return h5py.File(file_path, "r")


def get_session_datetime(snirf):
    """Returns the datetime of the session from a SNIRF file."""
    meta = snirf["nirs"]["metaDataTags"]
    date = _decode_str_array(meta["MeasurementDate"])
    time = _decode_str_array(meta["MeasurementTime"])
    datetime_str = f"{date}T{time}"
    return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ").astimezone(pytz.UTC)


def get_subject_id(snirf):
    """Returns the subject ID from a SNIRF file."""
    meta = snirf["nirs"]["metaDataTags"]
    subject_id = _decode_str_array(meta["SubjectID"])
    return subject_id


def get_subject_dateofbirth(snirf):
    """Returns the date of birth for the subject from a SNIRF file."""
    meta = snirf["nirs"]["metaDataTags"]
    dateofbirth = _decode_str_array(meta["DateOfBirth"])
    return datetime.strptime(dateofbirth, "%Y-%m-%d").astimezone(pytz.UTC)


def get_subject_sex(snirf):
    """Returns the sex of the subject from a SNIRF file."""
    meta = snirf["nirs"]["metaDataTags"]
    sex_id = _decode_str_array(meta["sex"])
    sex_map = {"1": "M", "2": "F"}
    if sex_id not in sex_map:
        raise KeyError(f"sex id: {sex_id} is not known")
    return sex_map[sex_id]


def get_source_labels(snirf):
    """Returns a list of the label of each source in the SNIRF file."""
    label_arr = snirf["nirs"]["probe"]["sourceLabels"][:]
    if len(label_arr.shape) == 2:
        cols = [label_arr[:, m] for m in range(label_arr.shape[1])]
        return [_decode_str_array(col) for col in cols]
    else:
        return [s.decode() for s in label_arr]


def get_source_pos(snirf):
    """Returns a list of the position of each source in the SNIRF file."""
    pos_arr = snirf["nirs"]["probe"]["sourcePos3D"][:]
    return [pos_arr[n] for n in range(pos_arr.shape[0])]


def get_detector_labels(snirf):
    """Returns a list of the label of each detector in the SNIRF file."""
    label_arr = snirf["nirs"]["probe"]["detectorLabels"][:]
    if len(label_arr.shape) == 2:
        cols = [label_arr[:, m] for m in range(label_arr.shape[1])]
        return [_decode_str_array(col) for col in cols]
    else:
        return [s.decode() for s in label_arr]


def get_detector_pos(snirf):
    """Returns a list of the position of each detector in the SNIRF file."""
    pos_arr = snirf["nirs"]["probe"]["detectorPos3D"][:]
    return [pos_arr[n] for n in range(pos_arr.shape[0])]


def get_wavelengths(snirf):
    """Returns a list of the channel wavelengths in the SNIRF file."""
    wavelengths = snirf["nirs"]["probe"]["wavelengths"][:]
    return wavelengths.flatten().astype(float)


def compile_channel_data(snirf):
    """Returns compiled information about each channel in the SNIRF file.

    Returns a dictionary of channel_id: value where each value is another dictionary
    containing the indices for the source, detector, and wavelength in the
    appropriate list.
    """

    def _to_zero_based_index(arr):
        return int(arr[:].item()) - 1

    def _extract_channel(ml):
        ch_data = snirf["nirs"]["data1"][ml]
        return {
            "source_idx": _to_zero_based_index(ch_data["sourceIndex"]),
            "detector_idx": _to_zero_based_index(ch_data["detectorIndex"]),
            "wavelength_idx": _to_zero_based_index(ch_data["wavelengthIndex"]),
        }

    channels = _map_channels_to_measurement_lists(snirf)
    return {channel_id: _extract_channel(ml) for channel_id, ml in channels.items()}


def _list_measurement_list_groups(snirf):
    """List the measurementLists in the SNIRF file."""
    return list(_map_channels_to_measurement_lists(snirf).values())


def _map_channels_to_measurement_lists(snirf):
    """Returns a map of measurementList index to measurementList group name."""
    prefix = "measurementList"
    data_keys = snirf["nirs"]["data1"].keys()
    mls = [k for k in data_keys if k.startswith(prefix)]

    def _extract_channel_id(ml):
        return int(ml[len(prefix) :])

    return {_extract_channel_id(ml): ml for ml in mls}


def get_snirf_measurement_data(snirf):
    """Returns the acquired measurement data in the SNIRF file."""
    return snirf["nirs"]["data1"]["dataTimeSeries"][:]


def get_snirf_measurement_timestamps(snirf):
    """Returns the timestamps of the measurement data in the SNIRF file."""
    return snirf["nirs"]["data1"]["time"][:].flatten()


def get_format_version(snirf):
    """Returns the SNIRF formatVersion listed in the SNIRF file."""
    return _decode_str_array(snirf["formatVersion"])


def check_units_of_measurement(snirf):
    """Verifies that the units of measurement listed in the SNIRF file match expection.

    Supported units of measurement:
    LengthUnit: 'm'
    TimeUnit: 's'
    FrequencyUnit: 'Hz'
    """
    expected_unit_map = {"LengthUnit": "m", "TimeUnit": "s", "FrequencyUnit": "Hz"}

    metadata = snirf["nirs"]["metaDataTags"]
    for uom_field, expected_uom in expected_unit_map.items():
        actual_uom = _decode_str_array(metadata[uom_field])
        if actual_uom != expected_uom:
            raise ValueError(
                f"Unsupported unit of measurement for {uom_field}:"
                f" expected '{expected_uom}', found '{actual_uom}'"
            )


def check_nirs_data_type_and_index(snirf):
    """Verifies that the data type in the SNIRF file corresponds to
    'Continuous Wave - Amplitude' data.
    """
    for ml in _list_measurement_list_groups(snirf):
        data_type = snirf["nirs"]["data1"][ml]["dataType"][()]
        data_type_index = snirf["nirs"]["data1"][ml]["dataTypeIndex"][()]
        if data_type != 1:
            raise ValueError(
                "Unsupported value for MeasurementList dataType: expected 1"
                f" (Continuous Wave - Amplitude), but found {data_type}."
            )
        if data_type_index != 1:
            raise ValueError(
                "Unsupported value for MeasurementList dataTypeIndex: expected 1,"
                f" but received a value of {data_type_index}."
            )


def _decode_str_array(str_arr):
    """Decodes string values from h5py Dataset arrays"""
    arr = str_arr[:].flatten()
    return "".join([s.decode() for s in arr])
