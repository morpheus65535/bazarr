# coding=utf-8

import logging
import rarfile

log = logging.getLogger(__name__)


class RarFile(rarfile.RarFile):
    def read(self, fname, psw=None):
        """
        read specific content of rarfile without parsing
        :param fname:
        :param psw:
        :return:
        """
        cmd = [rarfile.UNRAR_TOOL] + list(rarfile.ORIG_OPEN_ARGS)

        with rarfile.XTempFile(self._rarfile) as rf:
            log.debug(u"RAR CMD: %s", cmd + [rf, fname])
            p = rarfile.custom_popen(cmd + [rf, fname])
            output = p.communicate()[0]
            rarfile.check_returncode(p, output)

            return output
