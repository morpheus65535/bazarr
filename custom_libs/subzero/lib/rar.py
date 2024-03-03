# coding=utf-8

from __future__ import absolute_import
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
        exe = None
        try:
            rarfile.tool_setup(unrar=False, unar=True, bsdtar=False, force=True)
        except rarfile.RarCannotExec:
            try:
                rarfile.rarfile.tool_setup(unrar=True, unar=False, bsdtar=False, force=True)
            except rarfile.RarCannotExec:
                raise rarfile.RarCannotExec
            else:
                exe = rarfile.UNRAR_TOOL
        else:
            exe = rarfile.UNAR_TOOL
        finally:
            cmd = [exe] + list(rarfile.ORIG_OPEN_ARGS)

        with rarfile.XTempFile(self._rarfile) as rf:
            log.debug(u"RAR CMD: %s", cmd + [rf, fname])
            p = rarfile.custom_popen(cmd + [rf, fname])
            output = p.communicate()[0]
            rarfile.check_returncode(p, output)

            return output
