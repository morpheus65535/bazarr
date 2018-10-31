from asio.interfaces.posix import PosixInterface
from asio.interfaces.windows import WindowsInterface


class OpenParameters(object):
    def __init__(self):
        self.handlers = {}

        # Update handler_parameters with defaults
        self.posix()
        self.windows()

    def posix(self, mode=None, buffering=None):
        """
        :type mode: str
        :type buffering: int
        """
        self.handlers.update({PosixInterface: {
            'mode': mode,
            'buffering': buffering
        }})

    def windows(self, desired_access=WindowsInterface.GenericAccess.READ,
                share_mode=WindowsInterface.ShareMode.ALL,
                creation_disposition=WindowsInterface.CreationDisposition.OPEN_EXISTING,
                flags_and_attributes=0):

        """
        :param desired_access: WindowsInterface.DesiredAccess
        :type desired_access: int

        :param share_mode: WindowsInterface.ShareMode
        :type share_mode: int

        :param creation_disposition: WindowsInterface.CreationDisposition
        :type creation_disposition: int

        :param flags_and_attributes: WindowsInterface.Attribute, WindowsInterface.Flag
        :type flags_and_attributes: int
        """

        self.handlers.update({WindowsInterface: {
            'desired_access': desired_access,
            'share_mode': share_mode,
            'creation_disposition': creation_disposition,
            'flags_and_attributes': flags_and_attributes
        }})
