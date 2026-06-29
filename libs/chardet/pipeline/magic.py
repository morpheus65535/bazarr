"""Magic number detection for binary file types.

Note: ``from __future__ import annotations`` is intentionally omitted because
this module is compiled with mypyc, which does not support PEP 563 string
annotations.
"""

from chardet.pipeline import DetectionResult

# (prefix_bytes, mime_type) — longest prefix first to avoid shorter prefixes
# shadowing longer ones. All entries match at offset 0.
# Formats with sub-type logic (ftyp, RIFF, FORM, ZIP) are handled separately.
_MAGIC_NUMBERS: tuple[tuple[bytes, str], ...] = (
    # Images
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"MM\x00\x2a", "image/tiff"),
    (b"II\x2a\x00", "image/tiff"),
    (b"8BPS", "image/vnd.adobe.photoshop"),
    (b"qoif", "image/qoi"),
    (b"BM", "image/bmp"),
    (b"\xff\xd8\xff", "image/jpeg"),
    # JPEG XL: 12-byte container signature (must precede the 2-byte codestream)
    (
        b"\x00\x00\x00\x0c\x4a\x58\x4c\x20\x0d\x0a\x87\x0a",
        "image/jxl",
    ),
    # JPEG XL: 2-byte codestream signature
    (b"\xff\x0a", "image/jxl"),
    (
        b"\x00\x00\x01\x00",
        "image/vnd.microsoft.icon",
    ),  # ICO (not TTF — TTF is \x00\x01\x00\x00)
    # Audio/Video
    (b"ID3", "audio/mpeg"),
    (b"MThd", "audio/midi"),
    (b"OggS", "audio/ogg"),
    (b"fLaC", "audio/flac"),
    (b"\x1a\x45\xdf\xa3", "video/webm"),
    # Archives (ZIP handled separately below for subtype detection)
    (b"\x1f\x8b", "application/gzip"),
    (b"BZh", "application/x-bzip2"),
    (b"\xfd7zXZ\x00", "application/x-xz"),
    (b"7z\xbc\xaf\x27\x1c", "application/x-7z-compressed"),
    (b"Rar!\x1a\x07\x01\x00", "application/vnd.rar"),
    (b"Rar!\x1a\x07\x00", "application/vnd.rar"),
    (b"\x28\xb5\x2f\xfd", "application/zstd"),
    # Documents / Data
    (b"%PDF-", "application/pdf"),
    (b"SQLite format 3\x00", "application/x-sqlite3"),
    (b"ARROW1", "application/vnd.apache.arrow.file"),
    (b"PAR1", "application/vnd.apache.parquet"),
    (b"\x00asm", "application/wasm"),
    # Executables / Bytecode (cafebabe handled separately — shared by Java
    # class files and Mach-O fat binaries, disambiguated by bytes 4-7)
    (b"dex\n", "application/vnd.android.dex"),
    (b"\x7fELF", "application/x-elf"),
    (b"\xfe\xed\xfa\xce", "application/x-mach-binary"),
    (b"\xfe\xed\xfa\xcf", "application/x-mach-binary"),
    (b"\xce\xfa\xed\xfe", "application/x-mach-binary"),
    (b"\xcf\xfa\xed\xfe", "application/x-mach-binary"),
    (b"MZ", "application/vnd.microsoft.portable-executable"),
    # Fonts
    (b"wOFF", "font/woff"),
    (b"wOF2", "font/woff2"),
    (b"OTTO", "font/otf"),
    (b"\x00\x01\x00\x00", "font/ttf"),
)

# TAR archives have "ustar" at offset 257
_TAR_OFFSET = 257
_TAR_SIGNATURES: tuple[bytes, ...] = (b"ustar\x00", b"ustar ")

# RIFF container subtypes — determined by bytes 8-11
_RIFF_SUBTYPES: dict[bytes, str] = {
    b"WEBP": "image/webp",
    b"WAVE": "audio/wav",
    b"AVI ": "video/x-msvideo",
}

# FORM container subtypes (same layout as RIFF: 4-byte tag, 4-byte size, 4-byte type)
_FORM_SUBTYPES: dict[bytes, str] = {
    b"AIFF": "audio/aiff",
    b"AIFC": "audio/aiff",
}

# ZIP-based format detection — scan the first 4 KB for local file headers
# and classify based on entry filenames or content.  Many ZIP generators
# set the data-descriptor flag on every entry, making sequential header
# walking impossible without decompression.  Instead we search for
# PK\x03\x04 signatures and inspect the filename/content fields.
_ZIP_SIGNATURE = b"PK\x03\x04"
_ZIP_SCAN_LIMIT = 4096

# Filename prefix → MIME type (checked against each entry's filename)
_ZIP_FILENAME_PREFIXES: tuple[tuple[bytes, str], ...] = (
    # Office Open XML
    (b"xl/", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    (
        b"word/",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ),
    (
        b"ppt/",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ),
    # Java
    (b"META-INF/MANIFEST.MF", "application/java-archive"),
    # Android
    (b"AndroidManifest.xml", "application/vnd.android.package-archive"),
    # EPUB
    (b"META-INF/container.xml", "application/epub+zip"),
)

# Filename suffix → MIME type (checked against each entry's filename)
_ZIP_FILENAME_SUFFIXES: tuple[tuple[bytes, str], ...] = (
    # Python wheels: entries like "package-1.0.dist-info/WHEEL"
    (b".dist-info/", "application/x-wheel+zip"),
)

# OpenDocument MIME types recognized in the "mimetype" entry content.
_OPENDOCUMENT_MIMES: frozenset[bytes] = frozenset(
    {
        b"application/vnd.oasis.opendocument.text",
        b"application/vnd.oasis.opendocument.spreadsheet",
        b"application/vnd.oasis.opendocument.presentation",
        b"application/vnd.oasis.opendocument.graphics",
    }
)

# MP4/MOV/HEIC ftyp box — "ftyp" at offset 4
_FTYP_MARKER = b"ftyp"
_FTYP_OFFSET = 4
# Brand → MIME type for image ftyp brands
_FTYP_AVIF_BRANDS: frozenset[bytes] = frozenset({b"avif", b"avis"})
_FTYP_HEIC_BRANDS: frozenset[bytes] = frozenset({b"heic", b"heix"})
_FTYP_HEIF_BRANDS: frozenset[bytes] = frozenset({b"mif1", b"msf1"})
_FTYP_AUDIO_BRANDS: frozenset[bytes] = frozenset({b"M4A ", b"M4B ", b"F4A "})
_FTYP_QUICKTIME_BRANDS: frozenset[bytes] = frozenset({b"qt  "})

# Java class file vs Mach-O fat binary — both start with \xca\xfe\xba\xbe.
# Bytes 4-7 disambiguate: Mach-O fat stores nfat_arch (big-endian uint32,
# typically 2-5), while Java class stores minor_version (uint16) +
# major_version (uint16, 45+ for Java 1.1 through modern Java).
_CAFEBABE = b"\xca\xfe\xba\xbe"
_CAFEBABE_MAX_FAT_ARCHES = 20  # no real fat binary exceeds this


def _classify_zip(data: bytes) -> str:
    """Classify a ZIP file by scanning entry filenames and content.

    Scans for local file header signatures within the first
    ``_ZIP_SCAN_LIMIT`` bytes.  For each entry, checks the filename
    against known prefixes/suffixes, and for ``mimetype`` entries reads
    the uncompressed content to detect OpenDocument formats.

    **Limitation:** when an entry has the data-descriptor flag (bit 3)
    set, the compressed size in the header is 0 and we cannot skip past
    the entry content.  The scan may find spurious PK local file header
    signatures inside compressed data.  In practice deflate output rarely produces
    valid ZIP local file headers with recognizable filenames, so false
    positives are unlikely.
    """
    scan = data[:_ZIP_SCAN_LIMIT]
    offset = 0
    while True:
        idx = scan.find(_ZIP_SIGNATURE, offset)
        if idx == -1 or len(scan) < idx + 30:
            break
        name_len = int.from_bytes(scan[idx + 26 : idx + 28], "little")
        extra_len = int.from_bytes(scan[idx + 28 : idx + 30], "little")
        name_start = idx + 30
        if len(scan) < name_start + name_len:
            break
        name = scan[name_start : name_start + name_len]
        # Check filename prefixes
        for prefix, mime in _ZIP_FILENAME_PREFIXES:
            if name.startswith(prefix):
                return mime
        # Check filename suffixes
        for suffix, mime in _ZIP_FILENAME_SUFFIXES:
            if suffix in name:
                return mime
        # OpenDocument: "mimetype" entry with uncompressed content
        if name == b"mimetype":
            compression = int.from_bytes(scan[idx + 8 : idx + 10], "little")
            if compression == 0:  # stored (uncompressed)
                content_start = name_start + name_len + extra_len
                content_len = int.from_bytes(scan[idx + 22 : idx + 26], "little")
                if len(scan) >= content_start + content_len:
                    content = scan[content_start : content_start + content_len]
                    if content in _OPENDOCUMENT_MIMES:
                        return content.decode("ascii")
        # Advance past this entry's extra field and content to avoid
        # matching PK\x03\x04 that appears inside file data.  When the
        # data-descriptor flag (bit 3) is set, compressed_size in the
        # header is 0 — we still skip the extra field and hope the next
        # real header is found by the scan.
        flags = int.from_bytes(scan[idx + 6 : idx + 8], "little")
        content_size = (
            0 if flags & 0x0008 else int.from_bytes(scan[idx + 18 : idx + 22], "little")
        )
        offset = name_start + name_len + extra_len + content_size
    return "application/zip"


def _make_result(mime: str) -> DetectionResult:
    return DetectionResult(encoding=None, confidence=1.0, language=None, mime_type=mime)


def detect_magic(data: bytes) -> DetectionResult | None:
    """Check *data* for known binary file magic numbers.

    :param data: The raw byte data to examine.
    :returns: A :class:`DetectionResult` with ``encoding=None`` and the
        identified MIME type, or ``None`` if no magic number matches.
    """
    if not data:
        return None

    # Check ftyp box (MP4/MOV/HEIC/AVIF) — "ftyp" at offset 4.
    # Bytes 0-3 are the box size (big-endian uint32).  Valid ftyp boxes
    # have size >= 8 and <= file length.  The upper bound check prevents
    # false positives on text (ASCII bytes 0-3 produce huge box sizes
    # like 0x54686520 for "The ").
    if len(data) >= 12 and data[_FTYP_OFFSET : _FTYP_OFFSET + 4] == _FTYP_MARKER:
        box_size = int.from_bytes(data[:4], "big")
        if 8 <= box_size <= len(data):
            brand = data[8:12]
            if brand in _FTYP_AVIF_BRANDS:
                return _make_result("image/avif")
            if brand in _FTYP_HEIC_BRANDS:
                return _make_result("image/heic")
            if brand in _FTYP_HEIF_BRANDS:
                return _make_result("image/heif")
            if brand in _FTYP_AUDIO_BRANDS:
                return _make_result("audio/mp4")
            if brand in _FTYP_QUICKTIME_BRANDS:
                return _make_result("video/quicktime")
            return _make_result("video/mp4")

    # RIFF container — check subtype at bytes 8-11
    if data[:4] == b"RIFF" and len(data) >= 12:
        subtype = _RIFF_SUBTYPES.get(data[8:12])
        if subtype is not None:
            return _make_result(subtype)

    # FORM container (AIFF) — same layout as RIFF
    if data[:4] == b"FORM" and len(data) >= 12:
        subtype = _FORM_SUBTYPES.get(data[8:12])
        if subtype is not None:
            return _make_result(subtype)

    # ZIP-based format detection
    if data.startswith(_ZIP_SIGNATURE):
        return _make_result(_classify_zip(data))

    # Java class file vs Mach-O fat binary (both \xca\xfe\xba\xbe)
    if data[:4] == _CAFEBABE and len(data) >= 8:
        nfat_arch = int.from_bytes(data[4:8], "big")
        if nfat_arch <= _CAFEBABE_MAX_FAT_ARCHES:
            return _make_result("application/x-mach-binary")
        return _make_result("application/java-vm")

    # Fixed-offset magic numbers (all at offset 0)
    for prefix, mime in _MAGIC_NUMBERS:
        if data.startswith(prefix):
            return _make_result(mime)

    # TAR archive — "ustar" at offset 257
    if len(data) >= _TAR_OFFSET + 6:
        tar_sig = data[_TAR_OFFSET : _TAR_OFFSET + 6]
        if tar_sig in _TAR_SIGNATURES:
            return _make_result("application/x-tar")

    return None
