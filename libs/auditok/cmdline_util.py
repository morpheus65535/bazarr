import sys
import logging
from collections import namedtuple
from . import workers
from .util import AudioDataSource
from .io import player_for

_AUDITOK_LOGGER = "AUDITOK_LOGGER"
KeywordArguments = namedtuple(
    "KeywordArguments", ["io", "split", "miscellaneous"]
)


def make_kwargs(args_ns):
    if args_ns.save_stream is None:
        record = args_ns.plot or (args_ns.save_image is not None)
    else:
        record = False
    try:
        use_channel = int(args_ns.use_channel)
    except (ValueError, TypeError):
        use_channel = args_ns.use_channel

    io_kwargs = {
        "input": args_ns.input,
        "audio_format": args_ns.input_format,
        "max_read": args_ns.max_read,
        "block_dur": args_ns.analysis_window,
        "sampling_rate": args_ns.sampling_rate,
        "sample_width": args_ns.sample_width,
        "channels": args_ns.channels,
        "use_channel": use_channel,
        "save_stream": args_ns.save_stream,
        "save_detections_as": args_ns.save_detections_as,
        "export_format": args_ns.output_format,
        "large_file": args_ns.large_file,
        "frames_per_buffer": args_ns.frame_per_buffer,
        "input_device_index": args_ns.input_device_index,
        "record": record,
    }

    split_kwargs = {
        "min_dur": args_ns.min_duration,
        "max_dur": args_ns.max_duration,
        "max_silence": args_ns.max_silence,
        "drop_trailing_silence": args_ns.drop_trailing_silence,
        "strict_min_dur": args_ns.strict_min_duration,
        "energy_threshold": args_ns.energy_threshold,
    }

    miscellaneous = {
        "echo": args_ns.echo,
        "progress_bar": args_ns.progress_bar,
        "command": args_ns.command,
        "quiet": args_ns.quiet,
        "printf": args_ns.printf,
        "time_format": args_ns.time_format,
        "timestamp_format": args_ns.timestamp_format,
    }
    return KeywordArguments(io_kwargs, split_kwargs, miscellaneous)


def make_logger(stderr=False, file=None, name=_AUDITOK_LOGGER):
    if not stderr and file is None:
        return None
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if stderr:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

    if file is not None:
        handler = logging.FileHandler(file, "w")
        fmt = logging.Formatter("[%(asctime)s] | %(message)s")
        handler.setFormatter(fmt)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
    return logger


def initialize_workers(logger=None, **kwargs):
    observers = []
    reader = AudioDataSource(source=kwargs["input"], **kwargs)
    if kwargs["save_stream"] is not None:
        reader = workers.StreamSaverWorker(
            reader,
            filename=kwargs["save_stream"],
            export_format=kwargs["export_format"],
        )
        reader.start()

    if kwargs["save_detections_as"] is not None:
        worker = workers.RegionSaverWorker(
            kwargs["save_detections_as"],
            kwargs["export_format"],
            logger=logger,
        )
        observers.append(worker)

    if kwargs["echo"]:
        player = player_for(reader)
        worker = workers.PlayerWorker(
            player, progress_bar=kwargs["progress_bar"], logger=logger
        )
        observers.append(worker)

    if kwargs["command"] is not None:
        worker = workers.CommandLineWorker(
            command=kwargs["command"], logger=logger
        )
        observers.append(worker)

    if not kwargs["quiet"]:
        print_format = (
            kwargs["printf"]
            .replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\\r", "\r")
        )
        worker = workers.PrintWorker(
            print_format, kwargs["time_format"], kwargs["timestamp_format"]
        )
        observers.append(worker)

    return reader, observers
