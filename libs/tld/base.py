from codecs import open as codecs_open
from urllib.request import urlopen
from typing import Optional

from .exceptions import (
    TldIOError,
    TldImproperlyConfigured,
)
from .helpers import project_dir
from .registry import Registry

__author__ = 'Artur Barseghyan'
__copyright__ = '2013-2020 Artur Barseghyan'
__license__ = 'MPL-1.1 OR GPL-2.0-only OR LGPL-2.1-or-later'
__all__ = ('BaseTLDSourceParser',)


class BaseTLDSourceParser(metaclass=Registry):
    """Base TLD source parser."""

    uid: Optional[str] = None
    source_url: str
    local_path: str

    @classmethod
    def validate(cls):
        """Constructor."""
        if not cls.uid:
            raise TldImproperlyConfigured(
                "The `uid` property of the TLD source parser shall be defined."
            )

    @classmethod
    def get_tld_names(cls, fail_silently: bool = False, retry_count: int = 0):
        """Get tld names.

        :param fail_silently:
        :param retry_count:
        :return:
        """
        cls.validate()
        raise NotImplementedError(
            "Your TLD source parser shall implement `get_tld_names` method."
        )

    @classmethod
    def update_tld_names(cls, fail_silently: bool = False) -> bool:
        """Update the local copy of the TLD file.

        :param fail_silently:
        :return:
        """
        try:
            remote_file = urlopen(cls.source_url)
            local_file = codecs_open(
                project_dir(cls.local_path),
                'wb',
                encoding='utf8'
            )
            local_file.write(remote_file.read().decode('utf8'))
            local_file.close()
            remote_file.close()
        except Exception as err:
            if fail_silently:
                return False
            raise TldIOError(err)

        return True
