from datetime import datetime

import h5py
import pytz


def load_snirf(file_path):
    return h5py.File(file_path, "r")


def decode_str_array(str_arr):
    arr = str_arr[:].flatten()
    return "".join([s.decode() for s in arr])


def get_session_datetime(snirf):
    meta = snirf["nirs"]["metaDataTags"]
    date = decode_str_array(meta["MeasurementDate"])
    time = decode_str_array(meta["MeasurementTime"])
    datetime_str = f"{date}T{time}"
    return datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ").astimezone(pytz.UTC)


def get_subject_id(snirf):
    meta = snirf["nirs"]["metaDataTags"]
    subject_id = decode_str_array(meta["SubjectID"])
    return subject_id


def get_subject_dateofbirth(snirf):
    meta = snirf["nirs"]["metaDataTags"]
    dateofbirth = decode_str_array(meta["DateOfBirth"])
    return datetime.strptime(dateofbirth, "%Y-%m-%d").astimezone(pytz.UTC)


def get_subject_sex(snirf):
    meta = snirf["nirs"]["metaDataTags"]
    sex_id = decode_str_array(meta["sex"])
    sex_map = {"1": "M", "2": "F"}
    if sex_id not in sex_map:
        raise KeyError(f"sex id: {sex_id} is not known")
    return sex_map[sex_id]


def extract_source_labels(snirf):
    label_arr = snirf["nirs"]["probe"]["sourceLabels"][:]
    if len(label_arr.shape) == 2:
        cols = [label_arr[:, m] for m in range(label_arr.shape[1])]
        return [decode_str_array(col) for col in cols]
    else:
        return [s.decode() for s in label_arr]


def extract_source_pos(snirf):
    pos_arr = snirf["nirs"]["probe"]["sourcePos3D"][:]
    return [pos_arr[n] for n in range(pos_arr.shape[0])]


def extract_detector_labels(snirf):
    label_arr = snirf["nirs"]["probe"]["detectorLabels"][:]
    if len(label_arr.shape) == 2:
        cols = [label_arr[:, m] for m in range(label_arr.shape[1])]
        return [decode_str_array(col) for col in cols]
    else:
        return [s.decode() for s in label_arr]


def extract_detector_pos(snirf):
    pos_arr = snirf["nirs"]["probe"]["detectorPos3D"][:]
    return [pos_arr[n] for n in range(pos_arr.shape[0])]


def check_units_of_measurement(snirf):
    expected_unit_map = {"LengthUnit": "m", "TimeUnit": "s", "FrequencyUnit": "Hz"}

    metadata = snirf["nirs"]["metaDataTags"]
    for uom_field, expected_uom in expected_unit_map.items():
        actual_uom = decode_str_array(metadata[uom_field])
        if actual_uom != expected_uom:
            raise ValueError(
                f"Unsupported unit of measurement for {uom_field}:"
                f" expected '{expected_uom}', found '{actual_uom}'"
            )


def check_nirs_data_type_and_index(snirf):
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


def extract_wavelengths(snirf):
    wavelengths = snirf["nirs"]["probe"]["wavelengths"][:]
    return wavelengths.flatten().astype(float)


def extract_channels(snirf):
    channels = _map_channels_to_measurement_lists(snirf)

    def to_zero_based_index(arr):
        return int(arr[:].item()) - 1

    def extract_channel(ml):
        ch_data = snirf["nirs"]["data1"][ml]
        return {
            "source_idx": to_zero_based_index(ch_data["sourceIndex"]),
            "detector_idx": to_zero_based_index(ch_data["detectorIndex"]),
            "wavelength_idx": to_zero_based_index(ch_data["wavelengthIndex"]),
        }

    return {channel_id: extract_channel(ml) for channel_id, ml in channels.items()}


def _list_measurement_list_groups(snirf):
    return list(_map_channels_to_measurement_lists(snirf).values())


def _map_channels_to_measurement_lists(snirf):
    prefix = "measurementList"
    data_keys = snirf["nirs"]["data1"].keys()
    mls = [k for k in data_keys if k.startswith(prefix)]

    def extract_channel_id(ml):
        return int(ml[len(prefix) :])

    return {extract_channel_id(ml): ml for ml in mls}


def get_snirf_data(snirf):
    return snirf["nirs"]["data1"]["dataTimeSeries"][:]


def get_snirf_timestamps(snirf):
    return snirf["nirs"]["data1"]["time"][:].flatten()


def get_format_version(snirf):
    return decode_str_array(snirf["formatVersion"])
