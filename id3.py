#!/usr/bin/env python
#coding:utf8
import datetime
import time
import logging
import os
import sys
import struct
import traceback

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fmt = logging.Formatter('%(asctime)s %(levelname)s: %(pathname)s:%(lineno)d %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(fmt=fmt)
logger.addHandler(handler)

NONE_GENRE = 255
GENRES = [
    # 0-19
    'Blues', 'Classic Rock', 'Country', 'Dance', 'Disco', 'Funk', 'Grunge', 'Hip - Hop', 'Jazz', 'Metal',
    'New Age', 'Oldies', 'Other', 'Pop', 'R&B', 'Rap', 'Reggae', 'Rock', 'Techno', 'Industrial',
    # 20-39
    'Alternative', 'Ska', 'Death Metal', 'Pranks', 'Soundtrack', 'Euro - Techno', 'Ambient', 'Trip - Hop', 'Vocal',
    'Jazz + Funk',
    'Fusion', 'Trance', 'Classical', 'Instrumental', 'Acid', 'House', 'Game', 'Sound Clip', 'Gospel', 'Noise',
    # 40-59
    'Alt Rock', 'Bass', 'Soul', 'Punk', 'Space', 'Meditative', 'Instrumental Pop', 'Instrumental Rock', 'Ethnic',
    'Gothic',
    'Darkwave', 'Techno - Industrial', 'Electronic', 'Pop - Folk', 'Eurodance', 'Dream', 'Southern Rock', 'Comedy',
    'Cult', 'Gangsta Rap',
    # 60-79
    'Top 40', 'Christian Rap', 'Pop / Funk', 'Jungle', 'Native American', 'Cabaret', 'New Wave', 'Psychedelic', 'Rave',
    'Showtunes',
    'Trailer', 'Lo - Fi', 'Tribal', 'Acid Punk', 'Acid Jazz', 'Polka', 'Retro', 'Musical', 'Rock & Roll', 'Hard Rock',
    # 80-99
    'Folk', 'Folk / Rock', 'National Folk', 'Swing', 'Fast - Fusion', 'Bebob', 'Latin', 'Revival', 'Celtic',
    'Bluegrass',
    'Avantgarde', 'Gothic Rock', 'Progressive Rock', 'Psychedelic Rock', 'Symphonic Rock', 'Slow Rock', 'Big Band',
    'Chorus', 'Easy Listening', 'Acoustic',
    # 100-119
    'Humour', 'Speech', 'Chanson', 'Opera', 'Chamber Music', 'Sonata', 'Symphony', 'Booty Bass', 'Primus',
    'Porn Groove',
    'Satire', 'Slow Jam', 'Club', 'Tango', 'Samba', 'Folklore', 'Ballad', 'Power Ballad', 'Rhythmic Soul', 'Freestyle',
    # 120-139
    'Duet', 'Punk Rock', 'Drum Solo', 'A Cappella', 'Euro - House', 'Dance Hall', 'Goa', 'Drum & Bass', 'Club - House',
    'Hardcore',
    'Terror', 'Indie', 'BritPop', 'Negerpunk', 'Polsk Punk', 'Beat', 'Christian Gangsta Rap', 'Heavy Metal',
    'Black Metal', 'Crossover',
    # 140-147
    'Contemporary Christian', 'Christian Rock', 'Merengue', 'Salsa', 'Thrash Metal', 'Anime', 'JPop', 'Synthpop'
]

ENCODINGS = [
    'ISO8859-1', 'UTF-16', 'UTF-16BE', 'UTF-8',
]


IDS = {
    #
    # v1.0
    #
    "TIT2": "title",
    "TPE1": "artist",
    "TALB": "album",
    "TYER": "year",  # date in iTunes
    "COMM": "comment",
    "TRCK": "track",
    "TCON": "genre",

    #
    # v1.1
    #
    "TPOS": "disc",

    #
    # v2.3+
    #
    "APIC": "cover",
    "TPE2": "albumArtist",
    "TPUB": "publisher",

    "PRIV": "[private]",

    "TXXX": "userDefined",

    # in iTunes
    "TDRC": "date",
    "TCOP": "copyright",
    "TDEN": "creationTime",
    "TSSE": "encoder",

    # ID3 Editor
    "TDRL": "podcastReleased",
    "TCAT": "podcastCategory",
    "TGID": "podcastIdentifier",
    "WFED": "podcastFeed",
    "PCST": "podcastDescription",

    "USLT": "unsychronizedLyric",
}


PICTURE_TYPES = {
    0x00: "Other",
    0x01: "32x32 pixels 'file icon' (PNG only)",
    0x02: "Other file icon",
    0x03: "Cover (front)",
    0x04: "Cover (back)",
    0x05: "Leaflet page",
    0x06: "Media (e.g. lable side of CD)",
    0x07: "Lead artist/lead performer/soloist",
    0x08: "Artist/performer",
    0x09: "Conductor",
    0x0a: "Band/Orchestra",
    0x0b: "Composer",
    0x0C: "Lyricist/text writer",
    0x0D: "Recording Location",
    0x0E: "During recording",
    0x0F: "During performance",
    0x10: "Movie/video screen capture",
    0x11: "A bright coloured fish",
    0x12: "Illustration",
    0x13: "Band/artist logotype",
    0x14: "Publisher/Studio logotype",
}


def getByValue(value, d):
    for k, v in d.iteritems():
        if v == value:
            return k


class HelperString(object):
    @staticmethod
    def to_uni(obj):
        if isinstance(obj, bytes):
            try:
                return obj.decode('utf-8')
            except UnicodeDecodeError:
                return obj.decode('gbk')
        elif isinstance(obj, (int, long)):
            return unicode(obj)
        elif isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        else:
            return obj

    @staticmethod
    def to_str(obj):
        if isinstance(obj, unicode):
            return obj.encode('utf-8')
        else:
            return obj

    @staticmethod
    def shorten(s, placeholder=u'...', max_legnth=64):
        if len(s) > len(placeholder) and len(s) > max_legnth:
            return s[:max_legnth-3] + placeholder + s[-len(placeholder):]
        return s

    @staticmethod
    def shorten_filename(filename, placeholder=u'...', max_length=64):
        filename = HelperString.to_uni(filename)

        if len(filename) > len(placeholder) and len(filename) > max_length:
            fn, ext = os.path.splitext(filename)
            shorten = fn[:max_length-len(placeholder)] + placeholder + fn[-len(placeholder):] + ext
        else:
            shorten = filename
        return shorten



class Tag(object):
    """ ID3 tag parser
    Reference
    - https://en.wikipedia.org/wiki/ID3
    """

    V1X_SIZE = 128

    FILE_ID_V1X = "TAG"
    FILE_ID_V2X = "ID3"

    HEADER_SIZE = 10
    FRAME_ID_SIZE = 4

    VERSION_MAJOR_SUPPORT = [3, 4]


    def __init__(self, versionX, versionMajor, revision=None, size=None):
        """
        For v1.1, versionX=1 versionMajor=1 revision=None,
        for v2.4.0, versionX=2 versionMajor=4 revision=0.
        """
        self.versionX = versionX
        self.versionMajor = versionMajor
        self.revision = revision

        self.flags = None
        # for v2.3.0, %abc00000
        self.unsynchronisation = False # a
        self.extendedHeader = False # b
        self.experimentalIndicator = False # c
        # for v2.4.0 %abcd0000
        self.footerPresent = False # d

        self.size = size

        self.frames = []


    @staticmethod
    def isV1x(fileobj):
        fileobj.seek(-Tag.V1X_SIZE, os.SEEK_END)
        rawTag = fileobj.read(Tag.V1X_SIZE)
        fileobj.seek(0, os.SEEK_SET)
        return len(rawTag) == Tag.V1X_SIZE and rawTag[:3] == Tag.FILE_ID_V1X

    @staticmethod
    def isV2x(fileobj, filesize):
        rawHeader = fileobj.read(Tag.HEADER_SIZE)
        fileId, versionMajor, revision, flags, size = struct.unpack("!3sBBBL", rawHeader)
        fileobj.seek(0, os.SEEK_SET)

        return fileId == Tag.FILE_ID_V2X and \
               versionMajor in [3, 4] and \
               revision == 0 and \
               size <= filesize

    @staticmethod
    def parseFromFilepath(filepath):
        with open(filepath) as fileobj:
            fstat = os.stat(filepath)
            return Tag.parseFromFile(fileobj=fileobj, filesize=fstat.st_size)

    @staticmethod
    def parseFromFile(fileobj, filesize):
        if Tag.isV2x(fileobj=fileobj, filesize=filesize):
            return Tag.parseV2FromFile(fileobj=fileobj)
        elif Tag.isV1x(fileobj=fileobj):
            return Tag.parseV1FromFile(fileobj=fileobj)

    @staticmethod
    def parseV1FromFile(fileobj):
        """
        Reference
         - http://id3.org/ID3v1
        """
        tag = Tag(versionX=1, versionMajor=0, size=Tag.V1X_SIZE)

        fileobj.seek(-Tag.V1X_SIZE, os.SEEK_END)
        rawTag = fileobj.read(Tag.V1X_SIZE)

        title = rawTag[3:33].strip('\x00 ')
        artist = rawTag[33:63].strip('\x00 ')
        album = rawTag[63:93].strip('\x00 ')
        year = rawTag[93:97].strip('\x00 ')
        comment = rawTag[97:127].strip('\x00 ')

        track = None
        if rawTag[125] == '\0' and rawTag[126] not in ['\0', ' ']:
            tag.versionMajor = 1
            track = ord(rawTag[126])

        genre = None
        try:
            genre = GENRES[ord(rawTag[127])]
        except IndexError:
            msg = "parse genre failed -%s-" % rawTag[127]
            logger.warn(msg)

        tag.frameAppend(FrameText(
            versionX=tag.versionX,
            versionMajor=tag.versionMajor,
            frameIDHuman="title",
            data=title)
        )
        tag.frameAppend(FrameText(
            versionX=tag.versionX,
            versionMajor=tag.versionMajor,
            frameIDHuman="artist",
            data=artist)
        )
        tag.frameAppend(FrameText(
            versionX=tag.versionX,
            versionMajor=tag.versionMajor,
            frameIDHuman="album",
            data=album)
        )
        tag.frameAppend(FrameText(
            versionX=tag.versionX,
            versionMajor=tag.versionMajor,
            frameIDHuman="year",
            data=year)
        )
        tag.frameAppend(FrameComment(
            versionX=tag.versionX,
            versionMajor=tag.versionMajor,
            frameIDHuman="comment",
            data=comment)
        )

        tag.frameAppend(FrameText(
            versionX=tag.versionX,
            versionMajor=tag.versionMajor,
            frameIDHuman="track",
            data=track)
        )
        tag.frameAppend(FrameText(
            versionX=tag.versionX,
            versionMajor=tag.versionMajor,
            frameIDHuman="genre",
            data=genre)
        )

        return tag

    @staticmethod
    def parseV2FromFile(fileobj):
        """
        Reference
            - http://id3.org/id3v2.3.0
            - http://id3.org/id3v2.4.0-structure
        """
        rawHeader = fileobj.read(Tag.HEADER_SIZE)
        if len(rawHeader) != Tag.HEADER_SIZE:
            msg = 'parse v2 header failed'
            logger.error(msg)
            return

        fileId, versionMajor, revision, flags, size = struct.unpack("!3sBBBL", rawHeader)

        # print '>> header  FID, version, flags, size'
        # print fileId, versionMajor, revision, flags, size

        if versionMajor in Tag.VERSION_MAJOR_SUPPORT:
            tag = Tag(versionX=2, versionMajor=versionMajor, revision=revision, size=size)
        else:
            msg = 'expected versionMajor in %s, got %s' % (Tag.VERSION_MAJOR_SUPPORT, versionMajor)
            logger.warn(msg)
            return

        if flags & (1 << 7):
            tag.unsynchronisation = True
        if flags & (1 << 6):
            tag.extendedHeader = True
        if flags & (1 << 5):
            tag.experimentalIndicator = True

        if tag.versionMajor >= 4:
            if flags & (1 << 4):
                tag.footerPresent = True

        bytesLeft = size

        while bytesLeft > 0:
            rawHeaderFrame = fileobj.read(Tag.HEADER_SIZE)
            bytesLeft -= len(rawHeaderFrame)

            if len(rawHeaderFrame) != Tag.HEADER_SIZE:
                msg = 'skip invalid frame header or padding'
                logger.debug(msg)
                break

            frameID, frameSize, frameFlags = struct.unpack("!4sLH", rawHeaderFrame)
            # print '>> frame, FID, size, flags'
            # print frameID, frameSize, frameFlags

            # if frameSize is 0:
            #     print repr(rawHeaderFrame), bytesLeft
            #     print repr(fileobj.read())

            if not Frame.validID(frameID):
                break
            elif len(frameID) != Tag.FRAME_ID_SIZE:
                break

            if frameID == "APIC":
                clsFrame = FrameAttachedPicture
            elif frameID == "COMM":
                clsFrame = FrameComment
            elif frameID[0] == "W":
                clsFrame = FrameURLLink
            elif frameID == "TXXX":
                clsFrame = FrameUserDefinedTextInformation
            elif frameID == "PRIV":
                clsFrame = FramePrivate
            elif frameID == "USLT":
                clsFrame = SynchronisedLyrics
            else:
                clsFrame = FrameText

            try:
                frame = clsFrame(
                    versionX=tag.versionX,
                    versionMajor=tag.versionMajor,
                    frameID=frameID,
                    flags=frameFlags,
                )
            except KeyError:
                # skip this frame
                rawFrameData = fileobj.read(frameSize)
                bytesLeft -= len(rawFrameData)

                msg = 'got unexpected frame -%s- -%s-' % (repr(rawHeaderFrame), repr(rawFrameData))
                logger.warn(msg)

                continue

            if tag.versionMajor == 3:
                # %abc00000 %ijk00000
                if frame.flags & (1 << (7 + 8)):
                    frame.tagAlterPreservation = True
                if frame.flags & (1 << (6 + 8)):
                    frame.fileAlterPreservation = True
                if frame.flags & (1 << (5 + 8)):
                    frame.readonly = True

                if frame.flags & (1 << 7):
                    frame.readonly = True

                if frame.flags & (1 << 6):
                    frame.compression = True

                    decompressedSize = struct.unpack("!L", fileobj.read(4))[0]
                    bytesLeft -= 4

                if frame.flags & (1 << 5):
                    frame.encryption = True

            elif tag.versionMajor == 4:
                # %0abc0000 %0h00kmnp
                if frame.flags & (1 << (6 + 8)):
                    frame.tagAlterPreservation = True
                if frame.flags & (1 << (5 + 8)):
                    frame.fileAlterPreservation = True
                if frame.flags & (1 << (4 + 8)):
                    frame.readonly = True

                if frame.flags & (1 << 6):
                    frame.groupingIdentity = True

                if frame.flags & (1 << 4):
                    frame.compression = True

                    decompressedSize = struct.unpack("!L", fileobj.read(4))[0]
                    bytesLeft -= 4

                if frame.flags & (1 << 3):
                    frame.encryption = True
                if frame.flags & (1 << 2):
                    frame.unsynchronisation = True
                if frame.flags & (1 << 1):
                    frame.dataLengthIndicator = True

            rawFrameData = fileobj.read(frameSize)
            # print '>> frame data'
            # print repr(rawFrameData)
            # print

            bytesLeft -= len(rawFrameData)

            frame.parseRawData(rawData=rawFrameData)
            tag.frameAppend(frame=frame)

        return tag

    @staticmethod
    def remove(filepath):
        tag = Tag.parseFromFilepath(filepath=filepath)
        if tag is not None:
            with open(filepath) as f:
                if tag.versionX == 1:
                    fstat = os.stat(filepath)
                    dataAudio = f.read(fstat.st_size - tag.size)
                elif tag.versionX == 2:
                    f.seek(tag.size, os.SEEK_SET)
                    dataAudio = f.read()
                else:
                    dataAudio = f.read()
        else:
            with open(filepath) as f:
                dataAudio = f.read()
        return dataAudio


    @property
    def version(self):
        if self.versionX == 1:
            return (self.versionX, self.versionMajor)
        else:
            return (self.versionX, self.versionMajor, self.revision)

    def __str__(self):
        return str(self.dumps(version=self.version))

    def dumps(self, version):
        versionX = version[0]
        versionMajor = version[1]
        revision = None
        if len(version) > 2:
            revision = version[2]

        if versionX == 1:
            chunks = [Tag.FILE_ID_V1X]

            f = self.getFrame(frameIDHuman="title")
            if f is not None:
                title = HelperString.to_str(f.data)[:30]
            else:
                title = '\x00' * 30
            chunks.append(title)

            f = self.getFrame(frameIDHuman="artist")
            if f is not None:
                artist = HelperString.to_str(f.data)[:30]
            else:
                artist = '\x00' * 30
            chunks.append(artist)

            f = self.getFrame(frameIDHuman="album")
            if f is not None:
                album = HelperString.to_str(f.data)[:30]
            else:
                album = '\x00' * 30
            chunks.append(album)

            f = self.getFrame(frameIDHuman="year")
            if f is not None:
                year = HelperString.to_str(f.data)[:4]
            else:
                year = '\x00' * 4
            chunks.append(year)

            f = self.getFrame(frameIDHuman="comment")
            if f is not None:
                comment = HelperString.to_str(f.data)[:30]
            else:
                comment = '\x00' * 30

            track = None
            f = self.getFrame(frameIDHuman="track")
            if f is not None:
                track = HelperString.to_str(f.data)

            if track is not None:
                if versionMajor == 1:
                    track = int(track.split('/')[0])
                    if 0 <= track and track <= 255:
                        segemnts = []
                        prefix = comment[:28]
                        if 28 - len(prefix):
                            segemnts.append(prefix)
                            segemnts.append( '\x00' * (28-len(prefix)))
                        else:
                            segemnts.append(prefix)

                        segemnts.append('\x00')
                        segemnts.append(chr(track))

                        comment = ''.join(segemnts)
            chunks.append(comment)

            f = self.getFrame(frameIDHuman="genre")
            if f is not None:
                genre = HelperString.to_str(f.data)
                try:
                    idx = GENRES.index(genre)
                    genre = idx
                except ValueError:
                    genre = NONE_GENRE
            else:
                genre = NONE_GENRE
            chunks.append(chr(genre))

            b = ''.join(chunks)
        elif versionX == 2:

            chunks = [Tag.FILE_ID_V2X]

            chunks.append(chr(versionMajor))
            chunks.append(chr(revision))

            flags = 0
            chunks.append(struct.pack("!B", flags))

            frames = []
            for f in self.frames:
                frames.append(str(f))
            framesInB = ''.join(frames)

            size = len(framesInB)
            chunks.append(struct.pack('!L', size))

            chunks.append(framesInB)

            b = ''.join(chunks)
        else:
            msg = 'not support version'
            logger.warn(msg)
            return

        return b

    def getFrame(self, frameID=None, frameIDHuman=None):
        assert not (frameID == None and frameIDHuman == None)

        if frameID is None:
            frameID = getByValue(frameIDHuman, IDS)

        if frameID is None:
            msg = 'get frame by ID in human -%s- failed' % frameIDHuman
            logger.error(msg)
            return

        for frame in self.frames:
            if frame.id == frameID:
                return frame

    def frameAppend(self, frame):
        self.frames.append(frame)

    def appendFrame(self, flags=None, rawData=None, data=None, frameID=None, frameIDHuman=None):
        assert not (frameID == None and frameIDHuman == None)

        if frameID is None:
            frameID = getByValue(frameIDHuman, IDS)

        if frameID is None:
            msg = 'get frame by ID in human -%s- failed' % frameIDHuman
            logger.error(msg)
            return

        found = self.getFrame(frameID=frameID, frameIDHuman=frameIDHuman)
        if found is None:
            if frameID == "COMM":
                clsFrame = FrameComment
            elif frameID == "APIC":
                clsFrame = FrameAttachedPicture
            else:
                clsFrame = FrameText

            frame = clsFrame(
                frameID=frameID,
                frameIDHuman=frameIDHuman,
                versionX=self.versionX,
                versionMajor=self.versionMajor,
                flags=flags,
                rawData=rawData,
            )
        else:
            frame = found
        frame.update(data=data)

        if found is None:
            self.frames.append(frame)

    def saveAs(self, filepath, version):
        b = self.dumps(version=version)

        with open(filepath, "wb+") as f:
            f.write(b)

        msg = 'CREATE %s' % filepath
        logger.debug(msg)

    def pprint(self):
        print 'tag v%s' % '.'.join(
            (str(i) for i in self.version)
        )

        for f in self.frames:
            data =  f.data
            if self.versionX == 1:
                try:
                    data = HelperString.to_uni(data)
                except:
                    traceback.print_exc(file=sys.stderr)
            # elif self.versionX == 2:
            #     if f.id != "APIC":
            #         data = f.data.decode(f.encoding)
            #     else:
            #         data = f.data
            # else:
            #     return

            if f.id == "APIC":
                    frameIDHuman = IDS[f.id]
                    print " %s : " % frameIDHuman
                    print "      mimeType : %s" % f.mimeType
                    print "      pictureType : %s" % PICTURE_TYPES[f.pictureType]
                    print "      description : %s" % f.description.decode(f.encoding)
                    print "      pictureData : <... %d bytes ...>" % len(f.data)

            elif f.id == "TXXX":
                print " !%s : %s" % (f.description, f.data)
            elif f.id == "COMM":
                    frameIDHuman = IDS[f.id]
                    print " %s : " % frameIDHuman
                    print "      language : %s" % f.language
                    print "      shortDescription : %s" % f.shortDescription
                    print "      data : %s" % f.data
            elif f.id[0] == "T":
                try:
                    frameIDHuman = IDS[f.id]
                    print " %s : %s" % (frameIDHuman, data)
                except KeyError:
                    print " [%s] : %s" % (f.id, data)
            else:
                try:
                    frameIDHuman = IDS[f.id]
                    print " %s : %s" % (frameIDHuman, data)
                except KeyError:
                    print " [%s] : %s" % (f.id, repr(data))

        print


class Frame(object):

    def __init__(self,
                 versionX,
                 versionMajor,
                 frameID=None,
                 frameIDHuman=None,
                 flags=None,
                 data=None,
                 rawData=None,
                 **kwargs):
        self.versionX = versionX
        self.versionMajor = versionMajor

        assert not (frameID is None and frameIDHuman is None)

        if frameID is None:
            frameID = getByValue(frameIDHuman, IDS)
        else:
            frameIDHuman = IDS[frameID]

        if frameID is None:
            msg = 'get frame by ID in human -%s- failed' % frameIDHuman
            logger.error(msg)
            raise Exception(msg)

        self.id = frameID
        assert Frame.validID(self.id)
        self.frameIDHuman = frameIDHuman

        self.flags = flags

        if self.versionX == 2 and versionMajor == 3:
            # for v2.3.0, %abc00000 %ijk00000

            ## Frame status flags
            self.tagAlterPreservation = False # a
            self.fileAlterPreservation = False # b
            self.readonly = False # c

            ## Frame format flags
            self.compression = False # i
            self.encryption = False # j
            self.groupingIdentity = False # k

        elif self.versionX == 2 and versionMajor == 4:
            # for v2.4.0, %0abc0000 %0h00kmnp

            ## Frame status flags
            self.tagAlterPreservation = False  # a
            self.fileAlterPreservation = False  # b
            self.readonly = False  # c

            ## Frame format flags
            self.groupingIdentity = False  # h

            self.compression = False  # k
            self.encryption = False  # m
            self.unsynchronisation = False # n
            self.dataLengthIndicator = False # p


        self.data = data
        self.rawData = rawData

        if self.flags is not None:
            self.parseFlags()

        if rawData is not None:
            self.parseRawData(rawData=rawData)

    def __str__(self):
        raise NotImplemented

    @property
    def isExperimental(self):
        return self.id[0] in ["X", "Y", "Z"]

    @staticmethod
    def validID(fid):
        CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        for i in fid:
            if i not in CHARS:
                return False
        return True

    def parseFlags(self):
        if self.flags is not None:
            if self.versionMajor == 2:
                if self.versionMajor == 3:
                    # %abc00000 %ijk00000
                    if self.flags & (1 << (7 + 8)):
                        self.tagAlterPreservation = True
                    if self.flags & (1 << (6 + 8)):
                        self.fileAlterPreservation = True
                    if self.flags & (1 << (5 + 8)):
                        self.readonly = True

                    if self.flags & (1 << 7):
                        self.readonly = True
                    if self.flags & (1 << 6):
                        self.compression = True

                    if self.flags & (1 << 5):
                        self.encryption = True

                elif self.versionMajor == 4:
                    # %0abc0000 %0h00kmnp
                    if self.flags & (1 << (6 + 8)):
                        self.tagAlterPreservation = True
                    if self.flags & (1 << (5 + 8)):
                        self.fileAlterPreservation = True
                    if self.flags & (1 << (4 + 8)):
                        self.readonly = True

                    if self.flags & (1 << 6):
                        self.groupingIdentity = True

                    if self.flags & (1 << 4):
                        self.compression = True
                    if self.flags & (1 << 3):
                        self.encryption = True
                    if self.flags & (1 << 2):
                        self.unsynchronisation = True
                    if self.flags & (1 << 1):
                        self.dataLengthIndicator = True

    def parseRawData(self, rawData):
        raise NotImplementedError


    def update(self, rawData=None, data=None):
        kwargs = dict()

        if rawData is None and data is None:
            return

        if rawData is not None:
            if self.versionX == 1:
                data = rawData
            elif self.versionX == 2:
                idx = ord(rawData[0])
                remain = rawData[1:]

                if idx < 0 or idx > len(ENCODINGS):
                    msg = 'encoding not support'
                    logger.warn(msg)
                    return

                encoding = ENCODINGS[idx]
                kwargs["encoding"] = encoding

                if encoding == 'UTF-8':
                    offset = 1
                else:
                    offset = 2

                if self.id == "COMM":
                    language = remain[:3]
                    remain = remain[3:]
                    if len(language) != 3:
                        return
                    kwargs['language'] = language

                    idx = remain.index('\x00')
                    shortDescription = remain[:idx]
                    remain = remain[idx + offset:]
                    kwargs['shortDescription'] = shortDescription

                    data = remain

                elif self.id == "APIC":
                    idx = remain.index('\x00')
                    mimeType = remain[:idx]
                    remain = remain[idx + 1:]
                    kwargs["mimeType"] = mimeType

                    pictureType = ord(remain[0])
                    remain = remain[1:]
                    kwargs["pictureType"] = pictureType

                    idx = remain.index('\x00')
                    description = remain[:idx]
                    remain = remain[idx + offset:]
                    kwargs["description"] = description

                    data = remain
                else:
                    data = remain
            else:
                return

        self.data = data
        self.rawData = rawData

        for k in kwargs:
            v = kwargs[k]
            setattr(self, k, v)
        return kwargs


class FrameText(Frame):

    def __init__(self, encoding=None,  **kwargs):
        super(FrameText, self).__init__(**kwargs)

        if self.versionX == 1:
            if encoding is None:
                encoding = 'ISO8859-1'

        elif self.versionX == 2:
            if self.versionMajor == 3:
                encoding = 'UTF-16'
            else:
                encoding = 'UTF-8'

        self.encoding = encoding

    def __str__(self):
        chunks = [self.id]

        segments = []
        encoding = ENCODINGS.index(self.encoding)
        segments.append(chr(encoding))

        dataU = HelperString.to_uni(self.data) + '\x00'
        dataDecoded = dataU.encode(self.encoding)
        segments.append(dataDecoded)
        dataB = ''.join(segments)

        size = len(dataB)
        chunks.append(struct.pack("!L", size))

        flags = 0
        chunks.append(struct.pack("!H", flags))

        chunks.append(dataB)

        return ''.join(chunks)

    def parseRawData(self, rawData):
        self.rawData = rawData

        if self.versionX == 1:
            self.data = self.rawData

        elif self.versionX == 2:
            idx = ord(rawData[0])
            remain = rawData[1:]

            if idx < 0 or idx > len(ENCODINGS):
                msg = 'encoding not support'
                logger.warn(msg)
                return

            self.encoding = ENCODINGS[idx]
            self.data = remain.decode(self.encoding).strip(' \x00')


class FramePrivate(Frame):
    def __init__(self, ownerIdentifier=None, privateData=None, **kwargs):
        super(FramePrivate, self).__init__(**kwargs)

        self.ownerIdentifier = ownerIdentifier
        self.data = privateData

    def parseRawData(self, rawData):
        self.rawData = rawData

        if self.versionX != 2:
            return

        offset = 1
        idx = rawData.index('\x00')
        self.ownerIdentifier = rawData[:idx]
        remain = rawData[idx+offset:]

        self.data = remain

    @property
    def privateData(self):
        return self.data



class FrameUserDefinedTextInformation(FrameText):
    def __init__(self, description="\x00", **kwargs):
        kwargs['frameID'] = "TXXX"
        super(FrameUserDefinedTextInformation, self).__init__(**kwargs)
        self.description = description
        self.data = None


    def __str__(self):
        chunks = [self.id]

        segments = []
        encoding = ENCODINGS.index(self.encoding)
        segments.append(chr(encoding))

        descriptionU = HelperString.to_uni(self.description) + '\x00'
        descriptionDecoded = descriptionU.encode(self.encoding)
        segments.append(descriptionDecoded)

        valueU = HelperString.to_uni(self.data) + '\x00'
        valueDecoded = valueU.encode(self.encoding)
        segments.append(valueDecoded)

        dataB = ''.join(segments)

        size = len(dataB)
        chunks.append(struct.pack("!L", size))

        flags = 0
        chunks.append(struct.pack("!H", flags))

        chunks.append(dataB)

        return ''.join(chunks)


    def parseRawData(self, rawData):
        self.rawData = rawData

        if self.versionX != 2:
            return

        idx = ord(rawData[0])
        remain = rawData[1:]

        if idx < 0 or idx > len(ENCODINGS):
            msg = 'encoding not support'
            logger.warn(msg)
            return

        self.encoding = ENCODINGS[idx]

        if self.encoding == 'UTF-16':
            spliter = '\x00\x00'
        else:
            spliter = '\x00'

        idx = remain.index(spliter)
        description = remain[:idx+1] # encoding with one char $00, so we do plus here
        remain = remain[idx+len(spliter)+1:]

        self.description = description.decode(self.encoding).strip(' \x00')

        value = remain
        self.data = value.decode(self.encoding).strip(' \x00')

    @property
    def value(self):
        return self.data


class FrameAttachedPicture(FrameText):
    def __init__(self, mimeType=None, pictureType=None, description=None, **kwargs):
        kwargs['frameID'] = "APIC"
        super(FrameAttachedPicture, self).__init__(**kwargs)
        self.mimeType = mimeType
        self.pictureType = pictureType
        self.description = description

    @property
    def pictureData(self):
        return self.data

    def parseRawData(self, rawData):
        if self.versionX != 2:
            msg = 'only tag v2.3.0+ support APIC frame'
            logger.warn(msg)
            return

        self.rawData = rawData

        idx = ord(rawData[0])
        remain = rawData[1:]

        if idx < 0 or idx > len(ENCODINGS):
            msg = 'encoding not support'
            logger.warn(msg)
            return

        self.encoding = ENCODINGS[idx]

        if self.encoding == 'UTF-8':
            offset = 1
        else:
            offset = 2

        idx = remain.index('\x00')
        mimeType = remain[:idx]
        remain = remain[idx + 1:]
        self.mimeType = mimeType

        pictureType = ord(remain[0])
        remain = remain[1:]
        self.pictureType = pictureType

        idx = remain.index('\x00')
        description = remain[:idx]
        remain = remain[idx + offset:]
        self.description = description.decode(self.encoding).strip(' \x00')

        self.data = remain


class FrameComment(FrameText):
    def __init__(self, language="eng", shortDescription="\x00", **kwargs):
        kwargs['frameID'] = "COMM"
        super(FrameComment, self).__init__(**kwargs)
        self.language = language
        self.shortDescription = shortDescription


    def __str__(self):
        chunks = [self.id]


        segments = []

        encoding = ENCODINGS.index(self.encoding)
        segments.append(chr(encoding))

        segments.append(self.language)

        shortDescriptionU = HelperString.to_uni(self.shortDescription) + '\x00'
        shortDescriptionDecoded = shortDescriptionU.encode(self.encoding)
        segments.append(shortDescriptionDecoded)

        dataDecoded = HelperString.to_uni(self.data).encode(self.encoding)
        segments.append(dataDecoded)

        dataB = ''.join(segments)


        size = len(dataB)
        chunks.append(struct.pack("!L", size))

        flags = 0
        chunks.append(struct.pack("!H", flags))

        chunks.append(dataB)

        return ''.join(chunks)


    def parseRawData(self, rawData):
        self.rawData = rawData

        if self.versionX == 1:
            self.data = self.rawData

        elif self.versionX == 2:
            idx = ord(rawData[0])
            remain = rawData[1:]

            if idx < 0 or idx > len(ENCODINGS):
                msg = 'encoding not support'
                logger.warn(msg)
                return

            encoding = ENCODINGS[idx]
            self.encoding = encoding

            if encoding == 'UTF-8':
                offset = 1
            else:
                offset = 2

            language = remain[:3]
            remain = remain[3:]
            if len(language) != 3:
                msg = 'got comment in unexpected structure %s' % repr(rawData)
                logger.warn(msg)
                return

            self.language = language

            idx = remain.index('\x00')
            shortDescription = remain[:idx]
            remain = remain[idx + offset:]
            self.shortDescription = shortDescription.decode(self.encoding).strip(' \x00')

            self.data = remain.decode(self.encoding).strip(' \x00')


class FrameURLLink(FrameText):
    def __init__(self, description="\x00", **kwargs):
        super(FrameURLLink, self).__init__(**kwargs)

        self.description = description

    def __str__(self):
        chunks = [self.id]

        segments = []

        if self.description is not None:
            encoding = ENCODINGS.index(self.encoding)
            segments.append(chr(encoding))

            descriptionU = HelperString.to_uni(self.description) + '\x00'
            descriptionDecoded = descriptionU.encode(self.encoding)
            segments.append(descriptionDecoded)

        dataDecoded = HelperString.to_uni(self.data).encode(self.encoding)
        segments.append(dataDecoded)

        dataB = ''.join(segments)


        size = len(dataB)
        chunks.append(struct.pack("!L", size))

        flags = 0
        chunks.append(struct.pack("!H", flags))

        chunks.append(dataB)

        return ''.join(chunks)


    def parseRawData(self, rawData):
        self.rawData = rawData

        if self.versionX != 2:
            return


        idx = ord(rawData[0])
        remain = rawData[1:]

        if idx < 0 or idx > len(ENCODINGS):
            self.data = remain
            return


        encoding = ENCODINGS[idx]
        self.encoding = encoding

        if encoding == 'UTF-8':
            offset = 1
        else:
            offset = 2

        idx = remain.index('\x00')
        description = remain[:idx]
        remain = remain[idx + offset:]
        self.description = description.decode(self.encoding).strip(' \x00')

        self.data = remain.decode(self.encoding)


class SynchronisedLyrics(Frame):

    def __init__(self, language="eng", contentDescriptor="\x00", **kwargs):
        kwargs['frameID'] = "USLT"
        super(SynchronisedLyrics, self).__init__(**kwargs)
        self.encoding = None
        self.language = language
        self.contentDescriptor = contentDescriptor

    @property
    def lyrics(self):
        return self.data

    def parseRawData(self, rawData):
        self.rawData = rawData

        if self.versionX != 2:
            return

        idx = ord(rawData[0])
        remain = rawData[1:]

        if idx < 0 or idx > len(ENCODINGS):
            msg = 'got unexpected encoding %s' % repr(idx)
            logger.warn(msg)
            return

        encoding = ENCODINGS[idx]
        self.encoding = encoding

        if encoding == 'UTF-8':
            offset = 1
        else:
            offset = 2


        language = remain[:3]
        remain = remain[3:]
        if len(language) != 3:
            msg = 'got comment in unexpected structure %s' % repr(rawData)
            logger.warn(msg)
            return

        self.language = language

        idx = remain.index('\x00')
        contentDescriptor = remain[:idx]
        remain = remain[idx + offset:]
        self.contentDescriptor = contentDescriptor.decode(self.encoding).strip(' \x00')

        self.data = remain.decode(self.encoding).strip(' \x00')


def tagRead(args):
    filepath = os.path.realpath(args.file)

    tag = Tag.parseV2FromFile(fileobj=file(filepath, 'rb'))
    if tag is not None:
        tag.pprint()
        return

    tag = Tag.parseV1FromFile(fileobj=file(filepath, 'rb'))
    if tag is not None:
        tag.pprint()
        return

    msg = 'tag not found'
    logger.debug(msg)


def tagRemove(args):
    filepath = os.path.realpath(args.file)
    prefix = os.path.dirname(filepath)

    b = Tag.remove(filepath)

    filename = os.path.basename(filepath)
    fn, ext = os.path.splitext(filename)

    filepathNew = os.path.join(prefix, "%s.cleaned%s" % (fn, ext))
    with open(filepathNew, "wb") as f:
        f.write(b)

    msg = "SAVE %s" % filepathNew
    logger.debug(msg)


def tagUpdate(args):
    version = args.version.split('.')
    version = ([int(i) for i in version])

    versionX, versionMajor = version[0], version[1]

    if args.file:
        filepath = os.path.realpath(args.file)
        tag = Tag.parseFromFilepath(filepath=filepath)

        if tag is None:
            msg = 'tag not found'
            logger.debug(msg)
            tag = Tag(versionX=versionX, versionMajor=versionMajor)

        pathFolder = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        fn, ext = os.path.splitext(filename)
        filepathNew = os.path.join(pathFolder, "%s%s" % (fn, ".id3"))
    else:
        tag = Tag(versionX=versionX, versionMajor=versionMajor)

        pathFolder = PWD
        fn = "%s" % (long(time.time() * 1000))
        filepathNew = os.path.join(pathFolder, "%s%s" % (fn, ".id3"))

    if args.title is not None:
        title = HelperString.to_uni(args.title)
        tag.appendFrame(frameIDHuman="title", data=title)

    if args.artist is not None:
        artist = HelperString.to_uni(args.artist)
        tag.appendFrame(frameIDHuman="artist", data=artist)

    if args.album is not None:
        album = HelperString.to_uni(args.album)
        tag.appendFrame(frameIDHuman="album", data=album)

    if args.year is not None:
        year = int(args.year)
        assert 1 <= year and year < 10000 and len(args.year) == 4
        year = HelperString.to_uni(args.year)
        tag.appendFrame(frameIDHuman="year", data=year)

    if args.comment is not None:
        comment = HelperString.to_uni(args.comment)
        tag.appendFrame(frameIDHuman="comment", data=comment)

    if args.track is not None:
        track = HelperString.to_uni(args.track)
        tag.appendFrame(frameIDHuman="track", data=track)

    if args.genre is not None:
        genre = HelperString.to_uni(args.genre)
        tag.appendFrame(frameIDHuman="genre", data=genre)

    if versionX == 2:
        if args.disc is not None:
            disc = HelperString.to_uni(args.disc)
            tag.appendFrame(frameIDHuman="disc", data=disc)

        if args.albumArtist is not None:
            albumArtist = HelperString.to_uni(args.albumArtist)
            tag.appendFrame(frameIDHuman="albumArtist", data=albumArtist)


    tag.saveAs(filepath=filepathNew, version=version)


def tagDump(args):
    filepath = os.path.realpath(args.file)
    fstat = os.stat(filepath)
    fileobj = file(filepath, 'rb')

    if Tag.isV2x(fileobj=fileobj, filesize=fstat.st_size):
        rawHeader = fileobj.read(Tag.HEADER_SIZE)
        fileId, versionMajor, revision, flags, size = struct.unpack("!3sBBBL", rawHeader)

        fileobj.seek(0, os.SEEK_SET)
        rawTag = fileobj.read(size + 10)

    elif Tag.isV1x(fileobj=fileobj):
        fileobj.seek(-Tag.V1X_SIZE, os.SEEK_END)
        rawTag = fileobj.read(Tag.V1X_SIZE)

    else:
        msg = 'not support tag version'
        logger.warn(msg)
        return

    pathFolder = PWD
    filepathNew = os.path.join(pathFolder, "%s%s" % (os.path.basename(filepath), ".id3"))
    with open(filepathNew, 'wb') as f:
        f.write(rawTag)

    msg = 'CREATE %s' % filepathNew
    logger.debug(msg)


if __name__ == '__main__':
    import argparse
    import logging

    PWD = os.path.dirname(os.path.realpath(__file__))

    parser = argparse.ArgumentParser(description="ID3 tag parser and reader")
    parser.add_argument('--verbose', action="store_true")

    parser.add_argument('--file', help='/full/path/to/audio.mp3')

    parser.add_argument('--read', action="store_true", default=True, help="parse and print tag")
    parser.add_argument('--remove', action="store_true", help="remove tag")

    #parser.add_argument('--update', action="store_true", help="update tag")
    parser.add_argument('--version', help="generate specify version tag")
    parser.add_argument('--title')
    parser.add_argument('--artist')
    parser.add_argument('--album')
    parser.add_argument('--year')
    parser.add_argument('--comment')
    parser.add_argument('--track')
    parser.add_argument('--genre')
    parser.add_argument('--disc')
    parser.add_argument('--albumArtist')

    parser.add_argument('--dump', action="store_true", help="read and dump tag from media file")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.file:
        filepath = os.path.realpath(args.file)
        if not os.path.exists(filepath):
            msg = '%s not exists' % filepath
            logger.warn(msg)
            exit(1)

        if args.remove:
            tagRemove(args=args)
        elif args.dump:
            tagDump(args=args)
        else:
            tagRead(args=args)
    # elif args.update:
    #     tagUpdate(args=args)
    else:
        parser.print_usage()
        exit(1)
