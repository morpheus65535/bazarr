from .base import AnticaptchaClient
from pkg_resources import get_distribution, DistributionNotFound
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
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
