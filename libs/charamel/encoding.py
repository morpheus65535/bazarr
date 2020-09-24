"""
🌏 Charamel: Truly Universal Encoding Detection in Python 🌎
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Licensed under Apache 2.0
"""
import encodings.aliases
import enum


@enum.unique
class Encoding(str, enum.Enum):
    """
    Python character encodings
    """

    ASCII = 'ascii'
    BIG_5 = 'big5'
    BIG_5_HKSCS = 'big5hkscs'
    CP_037 = 'cp037'
    CP_273 = 'cp273'
    CP_424 = 'cp424'
    CP_437 = 'cp437'
    CP_500 = 'cp500'
    CP_720 = 'cp720'
    CP_737 = 'cp737'
    CP_775 = 'cp775'
    CP_850 = 'cp850'
    CP_852 = 'cp852'
    CP_855 = 'cp855'
    CP_856 = 'cp856'
    CP_857 = 'cp857'
    CP_858 = 'cp858'
    CP_860 = 'cp860'
    CP_861 = 'cp861'
    CP_862 = 'cp862'
    CP_863 = 'cp863'
    CP_864 = 'cp864'
    CP_865 = 'cp865'
    CP_866 = 'cp866'
    CP_869 = 'cp869'
    CP_874 = 'cp874'
    CP_875 = 'cp875'
    CP_932 = 'cp932'
    CP_949 = 'cp949'
    CP_950 = 'cp950'
    CP_1006 = 'cp1006'
    CP_1026 = 'cp1026'
    CP_1125 = 'cp1125'
    CP_1140 = 'cp1140'
    CP_1250 = 'cp1250'
    CP_1251 = 'cp1251'
    CP_1252 = 'cp1252'
    CP_1253 = 'cp1253'
    CP_1254 = 'cp1254'
    CP_1255 = 'cp1255'
    CP_1256 = 'cp1256'
    CP_1257 = 'cp1257'
    CP_1258 = 'cp1258'
    EUC_JP = 'euc_jp'
    EUC_JIS_2004 = 'euc_jis_2004'
    EUC_JIS_X_0213 = 'euc_jisx0213'
    EUC_KR = 'euc_kr'
    GB_2312 = 'gb2312'
    GB_K = 'gbk'
    GB_18030 = 'gb18030'
    HZ = 'hz'
    ISO_2022_JP = 'iso2022_jp'
    ISO_2022_JP_1 = 'iso2022_jp_1'
    ISO_2022_JP_2 = 'iso2022_jp_2'
    ISO_2022_JP_2004 = 'iso2022_jp_2004'
    ISO_2022_JP_3 = 'iso2022_jp_3'
    ISO_2022_JP_EXT = 'iso2022_jp_ext'
    ISO_2022_KR = 'iso2022_kr'
    LATIN_1 = 'latin_1'
    ISO_8859_2 = 'iso8859_2'
    ISO_8859_3 = 'iso8859_3'
    ISO_8859_4 = 'iso8859_4'
    ISO_8859_5 = 'iso8859_5'
    ISO_8859_6 = 'iso8859_6'
    ISO_8859_7 = 'iso8859_7'
    ISO_8859_8 = 'iso8859_8'
    ISO_8859_9 = 'iso8859_9'
    ISO_8859_10 = 'iso8859_10'
    ISO_8859_11 = 'iso8859_11'
    ISO_8859_13 = 'iso8859_13'
    ISO_8859_14 = 'iso8859_14'
    ISO_8859_15 = 'iso8859_15'
    ISO_8859_16 = 'iso8859_16'
    JOHAB = 'johab'
    KOI_8_R = 'koi8_r'
    KOI_8_T = 'koi8_t'
    KOI_8_U = 'koi8_u'
    KZ_1048 = 'kz1048'
    MAC_CYRILLIC = 'mac_cyrillic'
    MAC_GREEK = 'mac_greek'
    MAC_ICELAND = 'mac_iceland'
    MAC_LATIN_2 = 'mac_latin2'
    MAC_ROMAN = 'mac_roman'
    MAC_TURKISH = 'mac_turkish'
    PTCP_154 = 'ptcp154'
    SHIFT_JIS = 'shift_jis'
    SHIFT_JIS_2004 = 'shift_jis_2004'
    SHIFT_JIS_X_0213 = 'shift_jisx0213'
    TIS_620 = 'tis_620'
    UTF_32 = 'utf_32'
    UTF_32_BE = 'utf_32_be'
    UTF_32_LE = 'utf_32_le'
    UTF_16 = 'utf_16'
    UTF_16_BE = 'utf_16_be'
    UTF_16_LE = 'utf_16_le'
    UTF_7 = 'utf_7'
    UTF_8 = 'utf_8'
    UTF_8_SIG = 'utf_8_sig'

    @classmethod
    def _missing_(cls, value):
        normalized = encodings.normalize_encoding(value).lower()
        normalized = encodings.aliases.aliases.get(normalized, normalized)
        if value != normalized:
            return cls(normalized)
        return super()._missing_(value)
