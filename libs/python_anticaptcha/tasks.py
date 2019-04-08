import base64
from .fields import BaseField


class BaseTask(object):
    def serialize(self, **result):
        return result


class ProxyMixin(BaseTask):
    def __init__(self, *args, **kwargs):
        self.proxy = kwargs.pop('proxy')
        self.userAgent = kwargs.pop('user_agent')
        self.cookies = kwargs.pop('cookies', '')
        super(ProxyMixin, self).__init__(*args, **kwargs)

    def serialize(self, **result):
        result = super(ProxyMixin, self).serialize(**result)
        result.update(self.proxy.serialize())
        result['userAgent'] = self.userAgent
        if self.cookies:
            result['cookies'] = self.cookies
        return result


class NoCaptchaTaskProxylessTask(BaseTask):
    type = "NoCaptchaTaskProxyless"
    websiteURL = None
    websiteKey = None
    websiteSToken = None

    def __init__(self, website_url, website_key, website_s_token=None, is_invisible=None):
        self.websiteURL = website_url
        self.websiteKey = website_key
        self.websiteSToken = website_s_token
        self.isInvisible = is_invisible

    def serialize(self):
        data = {'type': self.type,
                'websiteURL': self.websiteURL,
                'websiteKey': self.websiteKey}
        if self.websiteSToken is not None:
            data['websiteSToken'] = self.websiteSToken
        if self.isInvisible is not None:
            data['isInvisible'] = self.isInvisible
        return data


class FunCaptchaTask(ProxyMixin):
    type = "FunCaptchaTask"
    websiteURL = None
    websiteKey = None

    def __init__(self, website_url, website_key, *args, **kwargs):
        self.websiteURL = website_url
        self.websiteKey = website_key
        super(FunCaptchaTask, self).__init__(*args, **kwargs)

    def serialize(self, **result):
        result = super(FunCaptchaTask, self).serialize(**result)
        result.update({'type': self.type,
                       'websiteURL': self.websiteURL,
                       'websitePublicKey': self.websiteKey})
        return result


class NoCaptchaTask(ProxyMixin, NoCaptchaTaskProxylessTask):
    type = "NoCaptchaTask"


class ImageToTextTask(object):
    type = "ImageToTextTask"
    fp = None
    phrase = None
    case = None
    numeric = None
    math = None
    minLength = None
    maxLength = None

    def __init__(self, fp, phrase=None, case=None, numeric=None, math=None, min_length=None, max_length=None):
        self.fp = fp
        self.phrase = phrase
        self.case = case
        self.numeric = numeric
        self.math = math
        self.minLength = min_length
        self.maxLength = max_length

    def serialize(self):
        return {'type': self.type,
                'body': base64.b64encode(self.fp.read()).decode('utf-8'),
                'phrase': self.phrase,
                'case': self.case,
                'numeric': self.numeric,
                'math': self.math,
                'minLength': self.minLength,
                'maxLength': self.maxLength}


class CustomCaptchaTask(BaseTask):
    type = 'CustomCaptchaTask'
    imageUrl = None
    assignment = None
    form = None

    def __init__(self, imageUrl, form=None, assignment=None):
        self.imageUrl = imageUrl
        self.form = form or {}
        self.assignment = assignment

    def serialize(self):
        data = super(CustomCaptchaTask, self).serialize()
        data.update({'type': self.type,
                     'imageUrl': self.imageUrl})
        if self.form:
            forms = []
            for name, field in self.form.items():
                if isinstance(field, BaseField):
                    forms.append(field.serialize(name))
                else:
                    field = field.copy()
                    field['name'] = name
                    forms.append(field)
            data['forms'] = forms
        if self.assignment:
            data['assignment'] = self.assignment
        return data
