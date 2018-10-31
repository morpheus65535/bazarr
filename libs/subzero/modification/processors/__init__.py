# coding=utf-8


class Processor(object):
    """
    Processor base class
    """
    name = None
    parent = None
    supported = None
    enabled = True

    def __init__(self, name=None, parent=None, supported=None):
        self.name = name
        self.parent = parent
        self.supported = supported if supported else lambda parent: True

    @property
    def info(self):
        return self.name

    def process(self, content, debug=False, **kwargs):
        return content

    def __repr__(self):
        return "Processor <%s %s>" % (self.__class__.__name__, self.info)

    def __str__(self):
        return repr(self)

    def __unicode__(self):
        return unicode(repr(self))


class FuncProcessor(Processor):
    func = None

    def __init__(self, func, name=None, parent=None, supported=None):
        super(FuncProcessor, self).__init__(name=name, supported=supported)
        self.func = func

    def process(self, content, debug=False, **kwargs):
        return self.func(content)
