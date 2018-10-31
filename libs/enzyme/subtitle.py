# -*- coding: utf-8 -*-
from .exceptions import ReadError
from .parsers import ebml
from .mkv import MKV
from .parsers import ebml
import logging
import codecs
import os
import io

__all__ = ['Subtitle']
logger = logging.getLogger(__name__)

class Subtitle(object):
    """Subtitle extractor for Matroska Video File.
    
    Currently only SRT subtitles stored without lacing are supported
    """

    def __init__(self, stream):
        """Read the available subtitles from a MKV file-like object"""
        self._stream = stream
        #Use the MKV class to parse the META information
        mkv = MKV(stream)
        self._timecode_scale = mkv.info.timecode_scale
        self._subtitles = mkv.get_srt_subtitles_track_by_language()

    def has_subtitle(self, language):
        return language in self._subtitles

    def write_subtitle_to_stream(self, language):
        """Write a single subtitle to stream or return None if language not available"""
        if language in self._subtitles:
            subtitle = self._subtitles[language]            
            return _write_track_to_srt_stream(self._stream,subtitle.number,self._timecode_scale)
            logger.info("Writing subtitle for language %s to stream",language)            
        else:
            logger.info("Subtitle for language %s not found",language)

    def write_subtitles_to_stream(self):
        """Write all available subtitles as streams to a dictionary with language as the key"""        
        subtitles = dict()
        for language in self._subtitles:
            subtitles[language] = self.write_subtitle_to_stream(language)
        return subtitles
            
def _write_track_to_srt_stream(mkv_stream, track, timecode_scale):
    
    srt_stream = io.StringIO()
    index = 0
    for cluster in _parse_segment(mkv_stream,track):
        for blockgroup in cluster.blockgroups:
            index = index + 1
            timeRange = _print_time_range(timecode_scale,cluster.timecode,blockgroup.block.timecode,blockgroup.duration)
            srt_stream.write(str(index) + '\n')
            srt_stream.write(timeRange + '\n')
            srt_stream.write(codecs.decode(blockgroup.block.data.read(),'utf-8') + '\n')
            srt_stream.write('\n')
    return srt_stream
            
def _parse_segment(stream,track):
    
    stream.seek(0)
    specs = ebml.get_matroska_specs()

    # Find all level 1 Cluster elements and its subelements. Speed up this process by excluding all other currently known level 1 elements
    try:
        segments = ebml.parse(stream, specs,include_element_names=['Segment','Cluster','BlockGroup','Timecode','Block','BlockDuration',],max_level=3)
    except ReadError:
        pass
    
    clusters = []
    for cluster in segments[0].data:
        _parse_cluster(track, clusters, cluster)
    return clusters

def _parse_cluster(track, clusters, cluster):

    blockgroups = []
    timecode = None
    for child in cluster.data:
        if child.name == 'BlockGroup':
            _parse_blockgroup(track, blockgroups, child)
        elif child.name == 'Timecode':
            timecode = child.data
    
    if len(blockgroups) > 0 and timecode != None:
        clusters.append(Cluster(timecode, blockgroups))

def _parse_blockgroup(track, blockgroups, blockgroup):
    
    block = None
    duration = None
    for child in blockgroup.data:
        if child.name == 'Block':
            block = Block.fromelement(child)
            if block.track != track:
                block = None
        elif child.name == 'BlockDuration':
            duration = child.data
    
    if duration != None and block != None:
        blockgroups.append(BlockGroup(block, duration))

def _print_time_range(timecode_scale,clusterTimecode,blockTimecode,duration):

    timecode_scale_ms = timecode_scale / 1000000 #Timecode
    rawTimecode = clusterTimecode + blockTimecode        
    startTimeMilleSeconds = (rawTimecode) * timecode_scale_ms
    endTimeMilleSeconds = (rawTimecode + duration) * timecode_scale_ms
    
    return _print_time(startTimeMilleSeconds) + " --> " + _print_time(endTimeMilleSeconds)

def _print_time(timeInMilleSeconds):

    timeInSeconds, milleSeconds = divmod(timeInMilleSeconds, 1000)
    timeInMinutes, seconds = divmod(timeInSeconds, 60)
    hours, minutes = divmod(timeInMinutes, 60)
    
    return '%d:%02d:%02d,%d' % (hours,minutes,seconds,milleSeconds)

class Cluster(object):
    
    def __init__(self,timecode=None, blockgroups=[]):
        self.timecode = timecode
        self.blockgroups = blockgroups

class BlockGroup(object):
    
    def __init__(self,block=None,duration=None):
        self.block = block
        self.duration = duration

class Block(object):
    
    def __init__(self, track=None, timecode=None, invisible=False, lacing=None, flags=None, data=None):
        self.track = track
        self.timecode = timecode
        self.invisible = invisible
        self.lacing = lacing
        self.flags = flags
        self.data = data
    
    @classmethod
    def fromelement(cls,element):
        stream = element.data
        track = ebml.read_element_size(stream)
        timecode = ebml.read_element_integer(stream,2)
        flags = ord(stream.read(1))
        
        invisible = bool(flags & 0x8)
        
        if (flags & 0x6):
            lacing = 'EBML'
        elif (flags & 0x4):
            lacing = 'fixed-size'
        elif (flags & 0x2):
            lacing = 'Xiph'
        else:
            lacing = None
    
        if lacing:
            raise ReadError('Laced blocks are not implemented yet')
        
        data = ebml.read_element_binary(stream, element.size - stream.tell())    
        return cls(track,timecode,invisible,lacing,flags,data)    

    def __repr__(self):
        return '<%s track=%d, timecode=%d, invisible=%d, lacing=%s>' % (self.__class__.__name__, self.track,self.timecode,self.invisible,self.lacing)

class SimpleBlock(Block):
    
    def __init__(self, track=None, timecode=None, keyframe=False, invisible=False, lacing=None, flags=None, data=None, discardable=False):
        super(SimpleBlock,self).__init__(track,timecode,invisible,lacing,flags,data)
        self.keyframe = keyframe
        self.discardable = discardable
        
    def fromelement(cls,element):
        simpleblock = super(SimpleBlock, cls).fromelement(element)
        simpleblock.keyframe = bool(simpleblock.flags & 0x80)
        simpleblock.discardable = bool(simpleblock.flags & 0x1)
        return simpleblock

    def __repr__(self):
        return '<%s track=%d, timecode=%d, keyframe=%d, invisible=%d, lacing=%s, discardable=%d>' % (self.__class__.__name__, self.track,self.timecode,self.keyframe,self.invisible,self.lacing,self.discardable)