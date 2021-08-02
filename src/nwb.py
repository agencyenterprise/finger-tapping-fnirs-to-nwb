from hdmf.common import DynamicTableRegion
from ndx_nirs import (
    NIRSChannelsTable,
    NIRSDetectorsTable,
    NIRSDevice,
    NIRSSeries,
    NIRSSourcesTable,
)
from pynwb import NWBFile, TimeSeries
from pynwb.file import Subject

from snirf import (
    check_nirs_data_type_and_index,
    check_units_of_measurement,
    extract_channels,
    extract_detector_labels,
    extract_detector_pos,
    extract_source_labels,
    extract_source_pos,
    extract_wavelengths,
    get_session_datetime,
    get_snirf_data,
    get_snirf_timestamps,
    get_subject_dateofbirth,
    get_subject_id,
    get_subject_sex,
)


def convert_to_nwb(
    snirf,
    *,
    file_identifier="N/A",
    session_description="not available",
    manufacturer="unknown",
    nirs_mode="continuous-wave",
    stim_data=None,
    notes=None,
    experimenter=None,
    experiment_description=None,
    institution=None,
    keywords=None,
    publications=None,
):
    check_units_of_measurement(snirf)
    check_nirs_data_type_and_index(snirf)

    sources = compile_sources_table(
        labels=extract_source_labels(snirf), positions=extract_source_pos(snirf)
    )
    detectors = compile_detectors_table(
        labels=extract_detector_labels(snirf), positions=extract_detector_pos(snirf)
    )

    channels_meta = extract_channels(snirf)
    wavelengths = extract_wavelengths(snirf)
    channels = compile_channels_table(
        channels_meta=channels_meta,
        sources=sources,
        detectors=detectors,
        wavelengths=wavelengths,
    )

    device = compile_device(
        channels=channels, manufacturer=manufacturer, nirs_mode=nirs_mode
    )
    nirs_series = compile_series(
        timestamps=get_snirf_timestamps(snirf),
        raw_data=get_snirf_data(snirf),
        channels=channels,
    )

    subject_id = get_subject_id(snirf)
    date_of_birth = get_subject_dateofbirth(snirf)
    sex = get_subject_sex(snirf)
    subject = compile_subject(
        subject_id=subject_id, date_of_birth=date_of_birth, sex=sex
    )

    nwb = NWBFile(
        session_description=session_description,
        identifier=file_identifier,
        session_start_time=get_session_datetime(snirf),
        subject=subject,
        devices=[device],
        experimenter=experimenter,
        experiment_description=experiment_description,
        institution=institution,
        keywords=keywords,
        notes=notes,
        related_publications=publications,
    )
    nwb.add_acquisition(nirs_series)
    if stim_data is not None:
        stim_timeseries = compile_stim_timeseries(stim_data)
        nwb.add_stimulus(stim_timeseries)

    return nwb


def compile_sources_table(*, labels, positions):
    table = NIRSSourcesTable()
    for label, pos in zip(labels, positions):
        table.add_row({"label": label, "x": pos[0], "y": pos[1], "z": pos[2]})
    return table


def compile_detectors_table(*, labels, positions):
    table = NIRSDetectorsTable()
    for label, pos in zip(labels, positions):
        table.add_row({"label": label, "x": pos[0], "y": pos[1], "z": pos[2]})
    return table


def compile_channels_table(*, channels_meta, sources, detectors, wavelengths):
    table = NIRSChannelsTable()
    for channel_id, channel in channels_meta.items():
        source_label = sources.label[channel["source_idx"]]
        detector_label = detectors.label[channel["detector_idx"]]
        source_wavelength = wavelengths[channel["wavelength_idx"]]
        table.add_row(
            label=f"{source_label}_{detector_label} {source_wavelength:.0f}",
            source=channel["source_idx"],
            detector=channel["detector_idx"],
            source_wavelength=source_wavelength,
        )
    table.source.table = sources
    table.detector.table = detectors
    return table


def compile_device(*, channels, manufacturer, nirs_mode):
    return NIRSDevice(
        name="nirs_device",
        description="Information about the NIRS device used in this session",
        manufacturer=manufacturer,
        channels=channels,
        sources=channels.source.table,
        detectors=channels.detector.table,
        nirs_mode=nirs_mode,
    )


def compile_series(*, timestamps, raw_data, channels):
    return NIRSSeries(
        name="nirs_data",
        description="The raw NIRS channel data",
        timestamps=timestamps,
        channels=DynamicTableRegion(
            name="channels",
            description="an ordered map to the channels in this NIRS series",
            table=channels,
            data=channels.id[:],
        ),
        data=raw_data,
        unit="V",
    )


def compile_subject(*, subject_id, date_of_birth, sex):
    return Subject(subject_id=subject_id, date_of_birth=date_of_birth, sex=sex)


def compile_stim_timeseries(stim_data):
    return TimeSeries(
        name="auditory",
        data=stim_data.trial_type.to_list(),
        timestamps=stim_data.onset.values,
        description=(
            "Auditory stimuli presented to the subject. The three data columns"
            " represent: 1. description of the stimulus, 2. duration of the"
            " stimulus (in seconds), and 3. the id representing the stimulus"
        ),
        comments="The duration of all stimuli is 5 seconds",
        unit="N/A",
    )
