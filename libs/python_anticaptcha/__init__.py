from .base import AnticaptchaClient
from .tasks import NoCaptchaTask, NoCaptchaTaskProxylessTask, ImageToTextTask, FunCaptchaTask
from .proxy import Proxy
from .exceptions import AnticaptchaException
from .fields import SimpleText, Image, WebLink, TextInput, Textarea, Checkbox, Select, Radio, ImageUpload

AnticatpchaException = AnticaptchaException