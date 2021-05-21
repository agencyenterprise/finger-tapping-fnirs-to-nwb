import pytz
from datetime import datetime

import h5py
import numpy as np


def load_snirf(file_path):
    return h5py.File(file_path, 'r')


def decode_str_array(str_arr):
    arr = str_arr[:].flatten()
    return ''.join([s.decode() for s in arr])


def get_session_datetime(snirf):
    meta = snirf['nirs']['metaDataTags']
    date = decode_str_array(meta['MeasurementDate'])
    time = decode_str_array(meta['MeasurementTime'])
    datetime_str = f'{date}T{time}'
    return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%SZ').astimezone(pytz.UTC)


def get_subject_id(snirf):
    meta = snirf['nirs']['metaDataTags']
    subject_id = decode_str_array(meta['SubjectID'])
    return subject_id


def extract_source_labels(snirf):
    label_arr = snirf['nirs']['probe']['sourceLabels'][:]
    if len(label_arr.shape) == 2:
        cols = [label_arr[:, m] for m in range(label_arr.shape[1])]
        return [decode_str_array(col) for col in cols]
    else:
        return [s.decode() for s in label_arr]


def extract_source_pos(snirf):
    pos_arr = snirf['nirs']['probe']['sourcePos3D'][:]
    return [pos_arr[n] for n in range(pos_arr.shape[0])]


def extract_detector_labels(snirf):
    label_arr = snirf['nirs']['probe']['detectorLabels'][:]
    if len(label_arr.shape) == 2:
        cols = [label_arr[:, m] for m in range(label_arr.shape[1])]
        return [decode_str_array(col) for col in cols]
    else:
        return [s.decode() for s in label_arr]


def extract_detector_pos(snirf):
    pos_arr = snirf['nirs']['probe']['detectorPos3D'][:]
    return [pos_arr[n] for n in range(pos_arr.shape[0])]


def extract_wavelengths(snirf):
    wavelengths = snirf['nirs']['probe']['wavelengths'][:]
    return wavelengths.flatten().astype(float)


def extract_channels(snirf):
    prefix = 'measurementList'
    data_keys = snirf['nirs']['data1'].keys()
    mls = [k for k in data_keys if k.startswith(prefix)]
    channels = {int(ml[len(prefix):]): ml for ml in mls}

    def to_zero_based_index(arr):
        return int(arr[:].item()) - 1

    def extract_channel(ml):
        ch_data = snirf['nirs']['data1'][ml]
        return {
            'source_idx': to_zero_based_index(ch_data['sourceIndex']),
            'detector_idx': to_zero_based_index(ch_data['detectorIndex']),
            'wavelength_idx': to_zero_based_index(ch_data['wavelengthIndex']),
        }

    return {channel_id: extract_channel(ml) for channel_id, ml in channels.items()}


def get_snirf_data(snirf):
    return snirf['nirs']['data1']['dataTimeSeries'][:]


def get_snirf_timestamps(snirf):
    return snirf['nirs']['data1']['time'][:].flatten()
