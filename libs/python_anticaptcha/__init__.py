from .base import AnticaptchaClient
try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import version, PackageNotFoundError
from .tasks import (
    NoCaptchaTaskProxylessTask,
    RecaptchaV2TaskProxyless,
    NoCaptchaTask,
    RecaptchaV2Task,
    FunCaptchaProxylessTask,
    FunCaptchaTask,
    ImageToTextTask,
    RecaptchaV3TaskProxyless,
    HCaptchaTaskProxyless,
    HCaptchaTask,
    RecaptchaV2EnterpriseTaskProxyless,
    RecaptchaV2EnterpriseTask,
    GeeTestTaskProxyless,
    GeeTestTask,
    AntiGateTaskProxyless,
    AntiGateTask
)
from .exceptions import AnticaptchaException

AnticatpchaException = AnticaptchaException

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    pass
