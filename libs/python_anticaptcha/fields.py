import six
from python_anticaptcha.exceptions import InvalidWidthException, MissingNameException


class BaseField(object):
    label = None
    labelHint = None

    def serialize(self, name=None):
        data = {}
        if self.label:
            data["label"] = self.label or False
        if self.labelHint:
            data["labelHint"] = self.labelHint or False
        return data


class NameBaseField(BaseField):
    name = None

    def serialize(self, name=None):
        data = super(NameBaseField, self).serialize(name)
        if name:
            data["name"] = name
        elif self.name:
            data["name"] = self.name
        else:
            raise MissingNameException(cls=self.__class__)
        return data


class SimpleText(BaseField):
    contentType = "text"

    def __init__(self, content, label=None, labelHint=None, width=None):
        self.label = label
        self.labelHint = labelHint

        self.content = content
        self.width = width

    def serialize(self, name=None):
        data = super(SimpleText, self).serialize(name)
        data["contentType"] = self.contentType
        data["content"] = self.content

        if self.width:
            if self.width not in [100, 50, 33, 25]:
                raise InvalidWidthException(self.width)
            data["inputOptions"] = {}
            data["width"] = self.width
        return data


class Image(BaseField):
    contentType = "image"

    def __init__(self, imageUrl, label=None, labelHint=None):
        self.label = label
        self.labelHint = labelHint
        self.imageUrl = imageUrl

    def serialize(self, name=None):
        data = super(Image, self).serialize(name)
        data["contentType"] = self.contentType
        data["content"] = self.imageUrl
        return data


class WebLink(BaseField):
    contentType = "link"

    def __init__(self, linkText, linkUrl, label=None, labelHint=None, width=None):
        self.label = label
        self.labelHint = labelHint

        self.linkText = linkText
        self.linkUrl = linkUrl

        self.width = width

    def serialize(self, name=None):
        data = super(WebLink, self).serialize(name)
        data["contentType"] = self.contentType

        if self.width:
            if self.width not in [100, 50, 33, 25]:
                raise InvalidWidthException(self.width)
            data["inputOptions"] = {}
            data["width"] = self.width

        data.update({"content": {"url": self.linkUrl, "text": self.linkText}})

        return data


class TextInput(NameBaseField):
    def __init__(self, placeHolder=None, label=None, labelHint=None, width=None):
        self.label = label
        self.labelHint = labelHint

        self.placeHolder = placeHolder

        self.width = width

    def serialize(self, name=None):
        data = super(TextInput, self).serialize(name)
        data["inputType"] = "text"

        data["inputOptions"] = {}

        if self.width:
            if self.width not in [100, 50, 33, 25]:
                raise InvalidWidthException(self.width)

            data["inputOptions"]["width"] = str(self.width)

        if self.placeHolder:
            data["inputOptions"]["placeHolder"] = self.placeHolder
        return data


class Textarea(NameBaseField):
    def __init__(
        self, placeHolder=None, rows=None, label=None, width=None, labelHint=None
    ):
        self.label = label
        self.labelHint = labelHint

        self.placeHolder = placeHolder
        self.rows = rows
        self.width = width

    def serialize(self, name=None):
        data = super(Textarea, self).serialize(name)
        data["inputType"] = "textarea"
        data["inputOptions"] = {}
        if self.rows:
            data["inputOptions"]["rows"] = str(self.rows)
        if self.placeHolder:
            data["inputOptions"]["placeHolder"] = self.placeHolder
        if self.width:
            data["inputOptions"]["width"] = str(self.width)
        return data


class Checkbox(NameBaseField):
    def __init__(self, text, label=None, labelHint=None):
        self.label = label
        self.labelHint = labelHint

        self.text = text

    def serialize(self, name=None):
        data = super(Checkbox, self).serialize(name)
        data["inputType"] = "checkbox"
        data["inputOptions"] = {"label": self.text}
        return data


class Select(NameBaseField):
    type = "select"

    def __init__(self, label=None, choices=None, labelHint=None):
        self.label = label
        self.labelHint = labelHint
        self.choices = choices or ()

    def get_choices(self):
        for choice in self.choices:
            if isinstance(choice, six.text_type):
                yield choice, choice
            else:
                yield choice

    def serialize(self, name=None):
        data = super(Select, self).serialize(name)
        data["inputType"] = self.type

        data["inputOptions"] = []
        for value, caption in self.get_choices():
            data["inputOptions"].append({"value": value, "caption": caption})

        return data


class Radio(Select):
    type = "radio"


class ImageUpload(NameBaseField):
    def __init__(self, label=None, labelHint=None):
        self.label = label
        self.labelHint = labelHint

    def serialize(self, name=None):
        data = super(ImageUpload, self).serialize(name)
        data["inputType"] = "imageUpload"
        return data
