import base64
from .fields import BaseField


class BaseTask(object):
    def serialize(self, **result):
        return result


class ProxyMixin(BaseTask):
    def __init__(self, *args, **kwargs):
        self.proxyType = kwargs.pop("proxy_type")
        self.userAgent = kwargs.pop("user_agent")
        self.proxyAddress = kwargs.pop("proxy_address")
        self.proxyPort = kwargs.pop("proxy_port")
        self.proxyLogin = kwargs.pop("proxy_login")
        self.proxyPassword = kwargs.pop("proxy_password")

        self.cookies = kwargs.pop("cookies", "")
        super(ProxyMixin, self).__init__(*args, **kwargs)

    def serialize(self, **result):
        result = super(ProxyMixin, self).serialize(**result)
        result["userAgent"] = self.userAgent
        result["proxyType"] = self.proxyType
        result["proxyAddress"] = self.proxyAddress
        result["proxyPort"] = self.proxyPort
        if self.proxyLogin:
            result["proxyLogin"] = self.proxyLogin
            result["proxyPassword"] = self.proxyPassword
        if self.cookies:
            result["cookies"] = self.cookies
        return result


class NoCaptchaTaskProxylessTask(BaseTask):
    type = "NoCaptchaTaskProxyless"
    websiteURL = None
    websiteKey = None
    websiteSToken = None
    recaptchaDataSValue = None

    def __init__(
        self,
        website_url,
        website_key,
        website_s_token=None,
        is_invisible=None,
        recaptcha_data_s_value=None,
    ):
        self.websiteURL = website_url
        self.websiteKey = website_key
        self.websiteSToken = website_s_token
        self.recaptchaDataSValue = recaptcha_data_s_value
        self.isInvisible = is_invisible

    def serialize(self):
        data = {
            "type": self.type,
            "websiteURL": self.websiteURL,
            "websiteKey": self.websiteKey,
        }
        if self.websiteSToken is not None:
            data["websiteSToken"] = self.websiteSToken
        if self.isInvisible is not None:
            data["isInvisible"] = self.isInvisible
        if self.recaptchaDataSValue is not None:
            data["recaptchaDataSValue"] = self.recaptchaDataSValue
        return data


class NoCaptchaTask(ProxyMixin, NoCaptchaTaskProxylessTask):
    type = "NoCaptchaTask"


class FunCaptchaProxylessTask(BaseTask):
    type = "FunCaptchaTaskProxyless"
    websiteURL = None
    websiteKey = None

    def __init__(self, website_url, website_key, *args, **kwargs):
        self.websiteURL = website_url
        self.websiteKey = website_key
        super(FunCaptchaProxylessTask, self).__init__(*args, **kwargs)

    def serialize(self, **result):
        result = super(FunCaptchaProxylessTask, self).serialize(**result)
        result.update(
            {
                "type": self.type,
                "websiteURL": self.websiteURL,
                "websitePublicKey": self.websiteKey,
            }
        )
        return result


class FunCaptchaTask(ProxyMixin, FunCaptchaProxylessTask):
    type = "FunCaptchaTask"


class ImageToTextTask(object):
    type = "ImageToTextTask"
    fp = None
    phrase = None
    case = None
    numeric = None
    math = None
    minLength = None
    maxLength = None

    def __init__(
        self,
        fp,
        phrase=None,
        case=None,
        numeric=None,
        math=None,
        min_length=None,
        max_length=None,
    ):
        self.fp = fp
        self.phrase = phrase
        self.case = case
        self.numeric = numeric
        self.math = math
        self.minLength = min_length
        self.maxLength = max_length

    def serialize(self):
        return {
            "type": self.type,
            "body": base64.b64encode(self.fp.read()).decode("utf-8"),
            "phrase": self.phrase,
            "case": self.case,
            "numeric": self.numeric,
            "math": self.math,
            "minLength": self.minLength,
            "maxLength": self.maxLength,
        }


class CustomCaptchaTask(BaseTask):
    type = "CustomCaptchaTask"
    imageUrl = None
    assignment = None
    form = None

    def __init__(self, imageUrl, form=None, assignment=None):
        self.imageUrl = imageUrl
        self.form = form or {}
        self.assignment = assignment

    def serialize(self):
        data = super(CustomCaptchaTask, self).serialize()
        data.update({"type": self.type, "imageUrl": self.imageUrl})
        if self.form:
            forms = []
            for name, field in self.form.items():
                if isinstance(field, BaseField):
                    forms.append(field.serialize(name))
                else:
                    field = field.copy()
                    field["name"] = name
                    forms.append(field)
            data["forms"] = forms
        if self.assignment:
            data["assignment"] = self.assignment
        return data


class RecaptchaV3TaskProxyless(BaseTask):
    type = "RecaptchaV3TaskProxyless"
    websiteURL = None
    websiteKey = None
    minScore = None
    pageAction = None

    def __init__(self, website_url, website_key, min_score, page_action):
        self.websiteURL = website_url
        self.websiteKey = website_key
        self.minScore = min_score
        self.pageAction = page_action

    def serialize(self):
        data = super(RecaptchaV3TaskProxyless, self).serialize()
        data["type"] = self.type
        data["websiteURL"] = self.websiteURL
        data["websiteKey"] = self.websiteKey
        data["minScore"] = self.minScore
        data["pageAction"] = self.pageAction
        return data


class HCaptchaTaskProxyless(BaseTask):
    type = "HCaptchaTaskProxyless"
    websiteURL = None
    websiteKey = None

    def __init__(self, website_url, website_key, *args, **kwargs):
        self.websiteURL = website_url
        self.websiteKey = website_key
        super(HCaptchaTaskProxyless, self).__init__(*args, **kwargs)

    def serialize(self, **result):
        data = super(HCaptchaTaskProxyless, self).serialize(**result)
        data["type"] = self.type
        data["websiteURL"] = self.websiteURL
        data["websiteKey"] = self.websiteKey
        return data


class HCaptchaTask(ProxyMixin, HCaptchaTaskProxyless):
    type = "HCaptchaTask"


class SquareNetTask(BaseTask):
    type = "SquareNetTask"
    fp = None
    objectName = None
    rowsCount = None
    columnsCount = None

    def __init__(self, fp, objectName, rowsCount, columnsCount):
        self.fp = fp
        self.objectName = objectName
        self.rowsCount = rowsCount
        self.columnsCount = columnsCount

    def serialize(self):
        data = super(SquareNetTask, self).serialize()
        data["type"] = self.type
        data["body"] = base64.b64encode(self.fp.read()).decode("utf-8")
        data["objectName"] = self.objectName
        data["rowsCount"] = self.rowsCount
        data["columnsCount"] = self.columnsCount
        return data
