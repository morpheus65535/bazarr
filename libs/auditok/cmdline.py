#!/usr/bin/env python
# encoding: utf-8
'''
auditok.auditok -- Audio Activity Detection tool

auditok.auditok is a program that can be used for Audio/Acoustic activity detection.
It can read audio data from audio files as well as from built-in device(s) or standard input 


@author:     Mohamed El Amine SEHILI

@copyright:  2015-2018 Mohamed El Amine SEHILI

@license:    GPL v3

@contact:    amine.sehili@gmail.com
@deffield    updated: 01 Nov 2018
'''

import sys
import os

from optparse import OptionParser, OptionGroup
from threading import Thread
import tempfile
import wave
import time
import threading
import logging

try:
    import future
    from queue import Queue, Empty
except ImportError:
    if sys.version_info >= (3, 0):
        from queue import Queue, Empty
    else:
        from Queue import Queue, Empty

try:
    from pydub import AudioSegment
    WITH_PYDUB = True
except ImportError:
    WITH_PYDUB = False
    

from .core import StreamTokenizer
from .io import PyAudioSource, BufferAudioSource, StdinAudioSource, player_for
from .util import ADSFactory, AudioEnergyValidator
from auditok import __version__ as version

__all__ = []
__version__ = version
__date__ = '2015-11-23'
__updated__ = '2018-10-06'

DEBUG = 0
TESTRUN = 1
PROFILE = 0

LOGGER_NAME = "AUDITOK_LOGGER"

class AudioFileFormatError(Exception):
    pass

class TimeFormatError(Exception):
    pass

def file_to_audio_source(filename, filetype=None, **kwargs):
    
    lower_fname = filename.lower()
    rawdata = False
    
    if filetype is not None:
        filetype = filetype.lower()
    
    if filetype == "raw" or (filetype is None and lower_fname.endswith(".raw")):
        
        srate = kwargs.pop("sampling_rate", None)
        if srate is None:
            srate = kwargs.pop("sr", None)
            
        swidth = kwargs.pop("sample_width", None)
        if swidth is None:
            swidth = kwargs.pop("sw", None)
        
        ch = kwargs.pop("channels", None)
        if ch is None:
            ch = kwargs.pop("ch", None)
        
        if None in (swidth, srate, ch):
            raise Exception("All audio parameters are required for raw data") 
        
        data = open(filename).read()
        rawdata = True
        
    # try first with pydub
    if WITH_PYDUB:
        
        use_channel = kwargs.pop("use_channel", None)
        if use_channel is None:
            use_channel = kwargs.pop("uc", None)
        
        if use_channel is None:
            use_channel = 1
        else:
            try:
                use_channel = int(use_channel)
            except ValueError:
                pass
        
        if not isinstance(use_channel, (int)) and not use_channel.lower() in ["left", "right", "mix"] :
            raise ValueError("channel must be an integer or one of 'left', 'right' or 'mix'")
        
        asegment = None
        
        if rawdata:
            asegment = AudioSegment(data, sample_width=swidth, frame_rate=srate, channels=ch)
        if filetype in("wave", "wav") or (filetype is None and lower_fname.endswith(".wav")):
            asegment = AudioSegment.from_wav(filename)
        elif filetype == "mp3" or (filetype is None and lower_fname.endswith(".mp3")):
            asegment = AudioSegment.from_mp3(filename)
        elif filetype == "ogg" or (filetype is None and lower_fname.endswith(".ogg")):
            asegment = AudioSegment.from_ogg(filename)
        elif filetype == "flv" or (filetype is None and lower_fname.endswith(".flv")):
            asegment = AudioSegment.from_flv(filename)
        else:
            asegment = AudioSegment.from_file(filename)
            
        if asegment.channels > 1:
            
            if isinstance(use_channel, int):
                if use_channel > asegment.channels:
                    raise ValueError("Can not use channel '{0}', audio file has only {1} channels".format(use_channel, asegment.channels))
                else:
                    asegment = asegment.split_to_mono()[use_channel - 1]
            else:
                ch_lower = use_channel.lower()
                
                if ch_lower == "mix":
                    asegment = asegment.set_channels(1)
                    
                elif use_channel.lower() == "left":
                    asegment = asegment.split_to_mono()[0]
                    
                elif use_channel.lower() == "right":
                    asegment = asegment.split_to_mono()[1]
        
        return BufferAudioSource(data_buffer = asegment._data,
                                     sampling_rate = asegment.frame_rate,
                                     sample_width = asegment.sample_width,
                                     channels = asegment.channels)
    # fall back to standard python
    else:
        if rawdata:
            if ch != 1:
                raise ValueError("Cannot handle multi-channel audio without pydub")
            return BufferAudioSource(data, srate, swidth, ch)
    
        if filetype in ("wav", "wave") or (filetype is None and lower_fname.endswith(".wav")):
            
            wfp = wave.open(filename)
            
            ch = wfp.getnchannels()
            if ch != 1:
                wfp.close()
                raise ValueError("Cannot handle multi-channel audio without pydub")
           
            srate = wfp.getframerate()
            swidth = wfp.getsampwidth()
            data = wfp.readframes(wfp.getnframes())
            wfp.close()
            return BufferAudioSource(data, srate, swidth, ch)
        
        raise AudioFileFormatError("Cannot read audio file format")


def save_audio_data(data, filename, filetype=None, **kwargs):
    
    lower_fname = filename.lower()
    if filetype is not None:
        filetype = filetype.lower()
        
    # save raw data
    if filetype == "raw" or (filetype is None and lower_fname.endswith(".raw")):
        fp = open(filename, "w")
        fp.write(data)
        fp.close()
        return
    
    # save other types of data
    # requires all audio parameters
    srate = kwargs.pop("sampling_rate", None)
    if srate is None:
        srate = kwargs.pop("sr", None)
        
    swidth = kwargs.pop("sample_width", None)
    if swidth is None:
        swidth = kwargs.pop("sw", None)
    
    ch = kwargs.pop("channels", None)
    if ch is None:
        ch = kwargs.pop("ch", None)
    
    if None in (swidth, srate, ch):
        raise Exception("All audio parameters are required to save no raw data")
        
    if filetype in ("wav", "wave") or (filetype is None and lower_fname.endswith(".wav")):
        # use standard python's wave module
        fp = wave.open(filename, "w")
        fp.setnchannels(ch)
        fp.setsampwidth(swidth)
        fp.setframerate(srate)
        fp.writeframes(data)
        fp.close()
    
    elif WITH_PYDUB:
        
        asegment = AudioSegment(data, sample_width=swidth, frame_rate=srate, channels=ch)
        asegment.export(filename, format=filetype)
    
    else:
        raise AudioFileFormatError("cannot write file format {0} (file name: {1})".format(filetype, filename))


def plot_all(signal, sampling_rate, energy_as_amp, detections=[], show=True, save_as=None):
    
    import matplotlib.pyplot as plt
    import numpy as np
    t = np.arange(0., np.ceil(float(len(signal))) / sampling_rate, 1./sampling_rate )
    if len(t) > len(signal):
        t = t[: len(signal) - len(t)]
    
    for start, end in detections:
        p = plt.axvspan(start, end, facecolor='g', ec = 'r', lw = 2,  alpha=0.4)
    
    line = plt.axhline(y=energy_as_amp, lw=1, ls="--", c="r", label="Energy threshold as normalized amplitude")
    plt.plot(t, signal)
    legend = plt.legend(["Detection threshold"], bbox_to_anchor=(0., 1.02, 1., .102), loc=1, fontsize=16)
    ax = plt.gca().add_artist(legend)

    plt.xlabel("Time (s)", fontsize=24)
    plt.ylabel("Amplitude (normalized)", fontsize=24)
    
    if save_as is not None:
        plt.savefig(save_as, dpi=120)
    
    if show:
        plt.show()


def seconds_to_str_fromatter(_format):
    """
    Accepted format directives: %i %s %m %h
    """
    # check directives are correct 
    
    if _format == "%S":
        def _fromatter(seconds):
            return "{:.2f}".format(seconds)
    
    elif _format == "%I":
        def _fromatter(seconds):
            return "{0}".format(int(seconds * 1000))
    
    else:
        _format = _format.replace("%h", "{hrs:02d}")
        _format = _format.replace("%m", "{mins:02d}")
        _format = _format.replace("%s", "{secs:02d}")
        _format = _format.replace("%i", "{millis:03d}")
        
        try:
            i = _format.index("%")
            raise TimeFormatError("Unknow time format directive '{0}'".format(_format[i:i+2]))
        except ValueError:
            pass
        
        def _fromatter(seconds):
            millis = int(seconds * 1000)
            hrs, millis = divmod(millis, 3600000)
            mins, millis = divmod(millis, 60000)
            secs, millis = divmod(millis, 1000)
            return _format.format(hrs=hrs, mins=mins, secs=secs, millis=millis)
    
    return _fromatter



class Worker(Thread):
    
    def __init__(self, timeout=0.2, debug=False, logger=None):
        self.timeout = timeout
        self.debug = debug
        self.logger = logger
        
        if self.debug and self.logger is None:
            self.logger = logging.getLogger(LOGGER_NAME)
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stdout)
            self.logger.addHandler(handler)
            
        self._inbox = Queue()
        self._stop_request = Queue()
        Thread.__init__(self)
    
    
    def debug_message(self, message):
        self.logger.debug(message)
        
    def _stop_requested(self):
        
        try:
            message = self._stop_request.get_nowait()
            if message == "stop":
                return True

        except Empty:
            return False
    
    def stop(self):
        self._stop_request.put("stop")
        self.join()
        
    def send(self, message):
        self._inbox.put(message)
    
    def _get_message(self):
        try:
            message = self._inbox.get(timeout=self.timeout)
            return message        
        except Empty:
            return None


class TokenizerWorker(Worker):
    
    END_OF_PROCESSING = "END_OF_PROCESSING"
    
    def __init__(self, ads, tokenizer, analysis_window, observers):
        self.ads = ads
        self.tokenizer = tokenizer
        self.analysis_window = analysis_window
        self.observers = observers
        self._inbox = Queue()
        self.count = 0
        Worker.__init__(self)
        
    def run(self):
        
        def notify_observers(data, start, end):
            audio_data = b''.join(data)
            self.count += 1
            
            start_time = start * self.analysis_window
            end_time = (end+1) * self.analysis_window
            duration = (end - start + 1) * self.analysis_window
            
            # notify observers
            for observer in self.observers:
                observer.notify({"id" : self.count,
                                 "audio_data" : audio_data,
                                 "start" : start,
                                 "end" : end,
                                 "start_time" : start_time,
                                 "end_time" : end_time,
                                 "duration" : duration}
                                )
        
        self.ads.open()
        self.tokenizer.tokenize(data_source=self, callback=notify_observers)
        for observer in self.observers:
            observer.notify(TokenizerWorker.END_OF_PROCESSING)
            
    def add_observer(self, observer):
        self.observers.append(observer)
       
    def remove_observer(self, observer):
        self.observers.remove(observer)
    
    def read(self):
        if self._stop_requested():
            return None
        else:
            return self.ads.read()
    
        
class PlayerWorker(Worker):
    
    def __init__(self, player, timeout=0.2, debug=False, logger=None):
        self.player = player
        Worker.__init__(self, timeout=timeout, debug=debug, logger=logger)
        
    def run(self):
        while True:
            if self._stop_requested():
                break
            
            message = self._get_message()
            if message is not None:
                if message == TokenizerWorker.END_OF_PROCESSING:
                    break
                
                audio_data = message.pop("audio_data", None)
                start_time = message.pop("start_time", None)
                end_time = message.pop("end_time", None)
                dur = message.pop("duration", None)
                _id = message.pop("id", None)
                
                if audio_data is not None:
                    if self.debug:
                        self.debug_message("[PLAY]: Detection {id} played (start:{start}, end:{end}, dur:{dur})".format(id=_id, 
                        start="{:5.2f}".format(start_time), end="{:5.2f}".format(end_time), dur="{:5.2f}".format(dur)))
                    self.player.play(audio_data)
    
    def notify(self, message):
        self.send(message)
        
               
class CommandLineWorker(Worker):
    
    def __init__(self, command, timeout=0.2, debug=False, logger=None):
        self.command = command
        Worker.__init__(self, timeout=timeout, debug=debug, logger=logger)
    
    def run(self):
        while True:
            if self._stop_requested():
                break
            
            message = self._get_message()
            if message is not None:
                if message == TokenizerWorker.END_OF_PROCESSING:
                    break
                
                audio_data = message.pop("audio_data", None)
                _id = message.pop("id", None)
                if audio_data is not None:
                    raw_audio_file = tempfile.NamedTemporaryFile(delete=False)
                    raw_audio_file.write(audio_data)
                    cmd = self.command.replace("$", raw_audio_file.name)
                    if self.debug:
                        self.debug_message("[CMD ]: Detection {id} command: {cmd}".format(id=_id, cmd=cmd))
                    os.system(cmd)
                    os.unlink(raw_audio_file.name)
                
    def notify(self, message):
        self.send(message)
        

class TokenSaverWorker(Worker):
    
    def __init__(self, name_format, filetype, timeout=0.2, debug=False, logger=None, **kwargs):
        self.name_format = name_format
        self.filetype = filetype
        self.kwargs = kwargs
        Worker.__init__(self, timeout=timeout, debug=debug, logger=logger)
    
    def run(self):
        while True:
            if self._stop_requested():
                break
            
            message = self._get_message()
            if message is not None:
                if message == TokenizerWorker.END_OF_PROCESSING:
                    break
                
                audio_data = message.pop("audio_data", None)
                start_time = message.pop("start_time", None)
                end_time = message.pop("end_time", None)
                _id = message.pop("id", None)
                if audio_data is not None and len(audio_data) > 0:
                    fname = self.name_format.format(N=_id, start = "{:.2f}".format(start_time), end = "{:.2f}".format(end_time))
                    try:
                        if self.debug:
                            self.debug_message("[SAVE]: Detection {id} saved as {fname}".format(id=_id, fname=fname))
                        save_audio_data(audio_data, fname, filetype=self.filetype, **self.kwargs)
                    except Exception as e:
                        sys.stderr.write(str(e) + "\n")
    
    def notify(self, message):
        self.send(message)


class LogWorker(Worker):
    
    def __init__(self, print_detections=False, output_format="{start} {end}",
                 time_formatter=seconds_to_str_fromatter("%S"), timeout=0.2, debug=False, logger=None):
        
        self.print_detections = print_detections
        self.output_format = output_format
        self.time_formatter = time_formatter
        self.detections = []
        Worker.__init__(self, timeout=timeout, debug=debug, logger=logger)
        
    def run(self):
        while True:
            if self._stop_requested():
                break
            
            message = self._get_message()
            
            if message is not None:
                
                if message == TokenizerWorker.END_OF_PROCESSING:
                    break
                
                audio_data = message.pop("audio_data", None)
                _id = message.pop("id", None)
                start = message.pop("start", None)
                end = message.pop("end", None)
                start_time = message.pop("start_time", None)
                end_time = message.pop("end_time", None)
                duration = message.pop("duration", None)
                if audio_data is not None and len(audio_data) > 0:
                    
                    if self.debug:
                        self.debug_message("[DET ]: Detection {id} (start:{start}, end:{end})".format(id=_id, 
                            start="{:5.2f}".format(start_time),
                            end="{:5.2f}".format(end_time)))
                    
                    if self.print_detections:
                        print(self.output_format.format(id = _id,
                            start = self.time_formatter(start_time),
                            end = self.time_formatter(end_time), duration = self.time_formatter(duration)))
                        
                    self.detections.append((_id, start, end, start_time, end_time))
                   
    
    def notify(self, message):
        self.send(message)



def main(argv=None):
    '''Command line options.'''

    program_name = os.path.basename(sys.argv[0])
    program_version = version
    program_build_date = "%s" % __updated__

    program_version_string = '%%prog %s (%s)' % (program_version, program_build_date)
    #program_usage = '''usage: spam two eggs''' # optional - will be autogenerated by optparse
    program_longdesc = '''''' # optional - give further explanation about what the program does
    program_license = "Copyright 2015-2018 Mohamed El Amine SEHILI                                            \
                Licensed under the General Public License (GPL) Version 3 \nhttp://www.gnu.org/licenses/"

    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        parser = OptionParser(version=program_version_string, epilog=program_longdesc, description=program_license)
        
        group = OptionGroup(parser, "[Input-Output options]")
        group.add_option("-i", "--input", dest="input", help="Input audio or video file. Use - for stdin [default: read from microphone using pyaudio]", metavar="FILE")
        group.add_option("-t", "--input-type", dest="input_type", help="Input audio file type. Mandatory if file name has no extension [default: %default]", type=str, default=None, metavar="String")
        group.add_option("-M", "--max_time", dest="max_time", help="Max data (in seconds) to read from microphone/file [default: read until the end of file/stream]", type=float, default=None, metavar="FLOAT")
        group.add_option("-O", "--output-main", dest="output_main", help="Save main stream as. If omitted main stream will not be saved [default: omitted]", type=str, default=None, metavar="FILE")
        group.add_option("-o", "--output-tokens", dest="output_tokens", help="Output file name format for detections. Use {N} and {start} and {end} to build file names, example: 'Det_{N}_{start}-{end}.wav'", type=str, default=None, metavar="STRING")
        group.add_option("-T", "--output-type", dest="output_type", help="Audio type used to save detections and/or main stream. If not supplied will: (1). guess from extension or (2). use wav format", type=str, default=None, metavar="STRING")
        group.add_option("-u", "--use-channel", dest="use_channel", help="Choose channel to use from a multi-channel audio file (requires pydub). 'left', 'right' and 'mix' are accepted values. [Default: 1 (i.e. 1st or left channel)]", type=str, default="1", metavar="STRING")
        parser.add_option_group(group)
        
        
        group = OptionGroup(parser, "[Tokenization options]", "Set tokenizer options and energy threshold.")
        group.add_option("-a", "--analysis-window", dest="analysis_window", help="Size of analysis window in seconds [default: %default (10ms)]", type=float, default=0.01, metavar="FLOAT")
        group.add_option("-n", "--min-duration", dest="min_duration", help="Min duration of a valid audio event in seconds [default: %default]", type=float, default=0.2, metavar="FLOAT")
        group.add_option("-m", "--max-duration", dest="max_duration", help="Max duration of a valid audio event in seconds [default: %default]", type=float, default=5, metavar="FLOAT")
        group.add_option("-s", "--max-silence", dest="max_silence", help="Max duration of a consecutive silence within a valid audio event in seconds [default: %default]", type=float, default=0.3, metavar="FLOAT")
        group.add_option("-d", "--drop-trailing-silence", dest="drop_trailing_silence", help="Drop trailing silence from a detection [default: keep trailing silence]",  action="store_true", default=False)
        group.add_option("-e", "--energy-threshold", dest="energy_threshold", help="Log energy threshold for detection [default: %default]", type=float, default=50, metavar="FLOAT")
        parser.add_option_group(group)
        
        
        group = OptionGroup(parser, "[Audio parameters]", "Define audio parameters if data is read from a headerless file (raw or stdin) or you want to use different microphone parameters.")        
        group.add_option("-r", "--rate", dest="sampling_rate", help="Sampling rate of audio data [default: %default]", type=int, default=16000, metavar="INT")
        group.add_option("-c", "--channels", dest="channels", help="Number of channels of audio data [default: %default]", type=int, default=1, metavar="INT")
        group.add_option("-w", "--width", dest="sample_width", help="Number of bytes per audio sample [default: %default]", type=int, default=2, metavar="INT")
        group.add_option("-I", "--input-device-index", dest="input_device_index", help="Audio device index [default: %default] - only when using PyAudio", type=int, default=None, metavar="INT")
        group.add_option("-F", "--audio-frame-per-buffer", dest="frame_per_buffer", help="Audio frame per buffer [default: %default] - only when using PyAudio", type=int, default=1024, metavar="INT")
        parser.add_option_group(group)
        
        group = OptionGroup(parser, "[Do something with detections]", "Use these options to print, play or plot detections.") 
        group.add_option("-C", "--command", dest="command", help="Command to call when an audio detection occurs. Use $ to represent the file name to use with the command (e.g. -C 'du -h $')", default=None, type=str, metavar="STRING")
        group.add_option("-E", "--echo", dest="echo", help="Play back each detection immediately using pyaudio [default: do not play]",  action="store_true", default=False)
        group.add_option("-p", "--plot", dest="plot", help="Plot and show audio signal and detections (requires matplotlib)",  action="store_true", default=False)
        group.add_option("", "--save-image", dest="save_image", help="Save plotted audio signal and detections as a picture or a PDF file (requires matplotlib)",  type=str, default=None, metavar="FILE")
        group.add_option("", "--printf", dest="printf", help="print detections, one per line, using a user supplied format (e.g. '[{id}]: {start} -- {end}'). Available keywords {id}, {start}, {end} and {duration}",  type=str, default="{id} {start} {end}", metavar="STRING")
        group.add_option("", "--time-format", dest="time_format", help="format used to print {start} and {end}. [Default= %default]. %S: absolute time in sec. %I: absolute time in ms. If at least one of (%h, %m, %s, %i) is used, convert time into hours, minutes, seconds and millis (e.g. %h:%m:%s.%i). Only required fields are printed",  type=str, default="%S", metavar="STRING")
        parser.add_option_group(group)
        
        parser.add_option("-q", "--quiet", dest="quiet", help="Do not print any information about detections [default: print 'id', 'start' and 'end' of each detection]",  action="store_true", default=False)
        parser.add_option("-D", "--debug", dest="debug", help="Print processing operations to STDOUT",  action="store_true", default=False)
        parser.add_option("", "--debug-file", dest="debug_file", help="Print processing operations to FILE",  type=str, default=None, metavar="FILE")
        
        

        # process options
        (opts, args) = parser.parse_args(argv)
        
        if opts.input == "-":
            asource = StdinAudioSource(sampling_rate = opts.sampling_rate,
                                       sample_width = opts.sample_width,
                                       channels = opts.channels)
        #read data from a file
        elif opts.input is not None:
            asource = file_to_audio_source(filename=opts.input, filetype=opts.input_type, uc=opts.use_channel)
        
        # read data from microphone via pyaudio
        else:
            try:
                asource = PyAudioSource(sampling_rate = opts.sampling_rate,
                                        sample_width = opts.sample_width,
                                        channels = opts.channels,
                                        frames_per_buffer = opts.frame_per_buffer,
                                        input_device_index = opts.input_device_index)
            except Exception:
                sys.stderr.write("Cannot read data from audio device!\n")
                sys.stderr.write("You should either install pyaudio or read data from STDIN\n")
                sys.exit(2)
               
        logger = logging.getLogger(LOGGER_NAME)
        logger.setLevel(logging.DEBUG)
        
        handler = logging.StreamHandler(sys.stdout)
        if opts.quiet or not opts.debug:
            # only critical messages will be printed
            handler.setLevel(logging.CRITICAL)
        else:
            handler.setLevel(logging.DEBUG)
        
        logger.addHandler(handler)
        
        if opts.debug_file is not None:
            logger.setLevel(logging.DEBUG)
            opts.debug = True
            handler = logging.FileHandler(opts.debug_file, "w")
            fmt = logging.Formatter('[%(asctime)s] | %(message)s')
            handler.setFormatter(fmt)
            handler.setLevel(logging.DEBUG)
            logger.addHandler(handler)
        
        record = opts.output_main is not None or opts.plot or opts.save_image is not None
                        
        ads = ADSFactory.ads(audio_source = asource, block_dur = opts.analysis_window, max_time = opts.max_time, record = record)
        validator = AudioEnergyValidator(sample_width=asource.get_sample_width(), energy_threshold=opts.energy_threshold)
        
        
        if opts.drop_trailing_silence:
            mode = StreamTokenizer.DROP_TRAILING_SILENCE
        else:
            mode = 0
        
        analysis_window_per_second = 1. / opts.analysis_window
        tokenizer = StreamTokenizer(validator=validator, min_length=opts.min_duration * analysis_window_per_second,
                                    max_length=int(opts.max_duration * analysis_window_per_second),
                                    max_continuous_silence=opts.max_silence * analysis_window_per_second,
                                    mode = mode)
        
        
        observers = []
        tokenizer_worker = None
        
        if opts.output_tokens is not None:
            
            try:
                # check user format is correct
                fname  = opts.output_tokens.format(N=0, start=0, end=0)
                
                # find file type for detections
                tok_type =  opts.output_type
                if tok_type is None:
                    tok_type = os.path.splitext(opts.output_tokens)[1][1:]
                if tok_type == "": 
                    tok_type = "wav"
                
                token_saver = TokenSaverWorker(name_format=opts.output_tokens, filetype=tok_type,
                                               debug=opts.debug, logger=logger, sr=asource.get_sampling_rate(),
                                               sw=asource.get_sample_width(),
                                               ch=asource.get_channels())
                observers.append(token_saver)
            
            except Exception:
                sys.stderr.write("Wrong format for detections file name: '{0}'\n".format(opts.output_tokens))
                sys.exit(2)
            
        if opts.echo:
            try:
                player = player_for(asource)
                player_worker = PlayerWorker(player=player, debug=opts.debug, logger=logger)
                observers.append(player_worker)
            except Exception:
                sys.stderr.write("Cannot get an audio player!\n")
                sys.stderr.write("You should either install pyaudio or supply a command (-C option) to play audio\n")
                sys.exit(2)
                
        if opts.command is not None and len(opts.command) > 0:
            cmd_worker = CommandLineWorker(command=opts.command, debug=opts.debug, logger=logger)
            observers.append(cmd_worker)
        
        if not opts.quiet or opts.plot is not None or opts.save_image is not None:    
            oformat = opts.printf.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
            converter = seconds_to_str_fromatter(opts.time_format)
            log_worker = LogWorker(print_detections = not opts.quiet, output_format=oformat,
                                   time_formatter=converter, logger=logger, debug=opts.debug)
            observers.append(log_worker)
        
        tokenizer_worker = TokenizerWorker(ads, tokenizer, opts.analysis_window, observers)
        
        def _save_main_stream():
            # find file type
            main_type =  opts.output_type
            if main_type is None:
                main_type = os.path.splitext(opts.output_main)[1][1:]
            if main_type == "": 
                main_type = "wav"
            ads.close()
            ads.rewind()
            data = ads.get_audio_source().get_data_buffer()
            if len(data) > 0:
                save_audio_data(data=data, filename=opts.output_main, filetype=main_type, sr=asource.get_sampling_rate(),
                                sw = asource.get_sample_width(),
                                ch = asource.get_channels())
        
        def _plot():
            import numpy as np
            ads.close()
            ads.rewind()
            data = ads.get_audio_source().get_data_buffer()
            signal = AudioEnergyValidator._convert(data, asource.get_sample_width())
            detections = [(det[3] , det[4]) for det in log_worker.detections]
            max_amplitude = 2**(asource.get_sample_width() * 8 - 1) - 1
            energy_as_amp = np.sqrt(np.exp(opts.energy_threshold * np.log(10) / 10)) / max_amplitude
            plot_all(signal / max_amplitude, asource.get_sampling_rate(), energy_as_amp, detections, show = opts.plot, save_as = opts.save_image)
        
        
        # start observer threads
        for obs in observers:
            obs.start()
        # start tokenization thread
        tokenizer_worker.start()
        
        while True:
            time.sleep(1)
            if len(threading.enumerate()) == 1:
                break
            
        tokenizer_worker = None
            
        if opts.output_main is not None:
            _save_main_stream()
        if opts.plot or opts.save_image is not None:
            _plot()
            
        return 0
            
    except KeyboardInterrupt:
        
        if tokenizer_worker is not None:
            tokenizer_worker.stop()
        for obs in observers:
            obs.stop()
            
        if opts.output_main is not None:
            _save_main_stream()
        if opts.plot or opts.save_image is not None:
            _plot()
        
        return 0

    except Exception as e:
        sys.stderr.write(program_name + ": " + str(e) + "\n")
        sys.stderr.write("for help use -h\n")
        
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'auditok.auditok_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())
