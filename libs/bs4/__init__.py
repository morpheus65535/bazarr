"""Beautiful Soup
Elixir and Tonic
"The Screen-Scraper's Friend"
http://www.crummy.com/software/BeautifulSoup/

Beautiful Soup uses a pluggable XML or HTML parser to parse a
(possibly invalid) document into a tree representation. Beautiful Soup
provides methods and Pythonic idioms that make it easy to navigate,
search, and modify the parse tree.

Beautiful Soup works with Python 2.7 and up. It works better if lxml
and/or html5lib is installed.

For more than you ever wanted to know about Beautiful Soup, see the
documentation:
http://www.crummy.com/software/BeautifulSoup/bs4/doc/

"""

__author__ = "Leonard Richardson (leonardr@segfault.org)"
__version__ = "4.8.0"
__copyright__ = "Copyright (c) 2004-2019 Leonard Richardson"
# Use of this source code is governed by the MIT license.
__license__ = "MIT"

__all__ = ['BeautifulSoup']

import os
import re
import sys
import traceback
import warnings

from .builder import builder_registry, ParserRejectedMarkup
from .dammit import UnicodeDammit
from .element import (
    CData,
    Comment,
    DEFAULT_OUTPUT_ENCODING,
    Declaration,
    Doctype,
    NavigableString,
    PageElement,
    ProcessingInstruction,
    ResultSet,
    SoupStrainer,
    Tag,
    )

# The very first thing we do is give a useful error if someone is
# running this code under Python 3 without converting it.
'You are trying to run the Python 2 version of Beautiful Soup under Python 3. This will not work.'!='You need to convert the code, either by installing it (`python setup.py install`) or by running 2to3 (`2to3 -w bs4`).'

class BeautifulSoup(Tag):
    """
    This class defines the basic interface called by the tree builders.

    These methods will be called by the parser:
      reset()
      feed(markup)

    The tree builder may call these methods from its feed() implementation:
      handle_starttag(name, attrs) # See note about return value
      handle_endtag(name)
      handle_data(data) # Appends to the current data node
      endData(containerClass=NavigableString) # Ends the current data node

    No matter how complicated the underlying parser is, you should be
    able to build a tree using 'start tag' events, 'end tag' events,
    'data' events, and "done with data" events.

    If you encounter an empty-element tag (aka a self-closing tag,
    like HTML's <br> tag), call handle_starttag and then
    handle_endtag.
    """
    ROOT_TAG_NAME = '[document]'

    # If the end-user gives no indication which tree builder they
    # want, look for one with these features.
    DEFAULT_BUILDER_FEATURES = ['html', 'fast']

    ASCII_SPACES = '\x20\x0a\x09\x0c\x0d'

    NO_PARSER_SPECIFIED_WARNING = "No parser was explicitly specified, so I'm using the best available %(markup_type)s parser for this system (\"%(parser)s\"). This usually isn't a problem, but if you run this code on another system, or in a different virtual environment, it may use a different parser and behave differently.\n\nThe code that caused this warning is on line %(line_number)s of the file %(filename)s. To get rid of this warning, pass the additional argument 'features=\"%(parser)s\"' to the BeautifulSoup constructor.\n"

    def __init__(self, markup="", features=None, builder=None,
                 parse_only=None, from_encoding=None, exclude_encodings=None,
                 **kwargs):
        """Constructor.

        :param markup: A string or a file-like object representing
        markup to be parsed.

        :param features: Desirable features of the parser to be used. This
        may be the name of a specific parser ("lxml", "lxml-xml",
        "html.parser", or "html5lib") or it may be the type of markup
        to be used ("html", "html5", "xml"). It's recommended that you
        name a specific parser, so that Beautiful Soup gives you the
        same results across platforms and virtual environments.

        :param builder: A TreeBuilder subclass to instantiate (or
        instance to use) instead of looking one up based on
        `features`. You only need to use this if you've implemented a
        custom TreeBuilder.

        :param parse_only: A SoupStrainer. Only parts of the document
        matching the SoupStrainer will be considered. This is useful
        when parsing part of a document that would otherwise be too
        large to fit into memory.

        :param from_encoding: A string indicating the encoding of the
        document to be parsed. Pass this in if Beautiful Soup is
        guessing wrongly about the document's encoding.

        :param exclude_encodings: A list of strings indicating
        encodings known to be wrong. Pass this in if you don't know
        the document's encoding but you know Beautiful Soup's guess is
        wrong.

        :param kwargs: For backwards compatibility purposes, the
        constructor accepts certain keyword arguments used in
        Beautiful Soup 3. None of these arguments do anything in
        Beautiful Soup 4; they will result in a warning and then be ignored.

        Apart from this, any keyword arguments passed into the BeautifulSoup
        constructor are propagated to the TreeBuilder constructor. This
        makes it possible to configure a TreeBuilder beyond saying
        which one to use.

        """

        if 'convertEntities' in kwargs:
            del kwargs['convertEntities']
            warnings.warn(
                "BS4 does not respect the convertEntities argument to the "
                "BeautifulSoup constructor. Entities are always converted "
                "to Unicode characters.")

        if 'markupMassage' in kwargs:
            del kwargs['markupMassage']
            warnings.warn(
                "BS4 does not respect the markupMassage argument to the "
                "BeautifulSoup constructor. The tree builder is responsible "
                "for any necessary markup massage.")

        if 'smartQuotesTo' in kwargs:
            del kwargs['smartQuotesTo']
            warnings.warn(
                "BS4 does not respect the smartQuotesTo argument to the "
                "BeautifulSoup constructor. Smart quotes are always converted "
                "to Unicode characters.")

        if 'selfClosingTags' in kwargs:
            del kwargs['selfClosingTags']
            warnings.warn(
                "BS4 does not respect the selfClosingTags argument to the "
                "BeautifulSoup constructor. The tree builder is responsible "
                "for understanding self-closing tags.")

        if 'isHTML' in kwargs:
            del kwargs['isHTML']
            warnings.warn(
                "BS4 does not respect the isHTML argument to the "
                "BeautifulSoup constructor. Suggest you use "
                "features='lxml' for HTML and features='lxml-xml' for "
                "XML.")

        def deprecated_argument(old_name, new_name):
            if old_name in kwargs:
                warnings.warn(
                    'The "%s" argument to the BeautifulSoup constructor '
                    'has been renamed to "%s."' % (old_name, new_name))
                value = kwargs[old_name]
                del kwargs[old_name]
                return value
            return None

        parse_only = parse_only or deprecated_argument(
            "parseOnlyThese", "parse_only")

        from_encoding = from_encoding or deprecated_argument(
            "fromEncoding", "from_encoding")

        if from_encoding and isinstance(markup, str):
            warnings.warn("You provided Unicode markup but also provided a value for from_encoding. Your from_encoding will be ignored.")
            from_encoding = None

        # We need this information to track whether or not the builder
        # was specified well enough that we can omit the 'you need to
        # specify a parser' warning.
        original_builder = builder
        original_features = features
            
        if isinstance(builder, type):
            # A builder class was passed in; it needs to be instantiated.
            builder_class = builder
            builder = None
        elif builder is None:
            if isinstance(features, str):
                features = [features]
            if features is None or len(features) == 0:
                features = self.DEFAULT_BUILDER_FEATURES
            builder_class = builder_registry.lookup(*features)
            if builder_class is None:
                raise FeatureNotFound(
                    "Couldn't find a tree builder with the features you "
                    "requested: %s. Do you need to install a parser library?"
                    % ",".join(features))

        # At this point either we have a TreeBuilder instance in
        # builder, or we have a builder_class that we can instantiate
        # with the remaining **kwargs.
        if builder is None:
            builder = builder_class(**kwargs)
            if not original_builder and not (
                    original_features == builder.NAME or
                    original_features in builder.ALTERNATE_NAMES
            ):
                if builder.is_xml:
                    markup_type = "XML"
                else:
                    markup_type = "HTML"

                # This code adapted from warnings.py so that we get the same line
                # of code as our warnings.warn() call gets, even if the answer is wrong
                # (as it may be in a multithreading situation).
                caller = None
                try:
                    caller = sys._getframe(1)
                except ValueError:
                    pass
                if caller:
                    globals = caller.f_globals
                    line_number = caller.f_lineno
                else:
                    globals = sys.__dict__
                    line_number= 1                    
                filename = globals.get('__file__')
                if filename:
                    fnl = filename.lower()
                    if fnl.endswith((".pyc", ".pyo")):
                        filename = filename[:-1]
                if filename:
                    # If there is no filename at all, the user is most likely in a REPL,
                    # and the warning is not necessary.
                    values = dict(
                        filename=filename,
                        line_number=line_number,
                        parser=builder.NAME,
                        markup_type=markup_type
                    )
                    warnings.warn(self.NO_PARSER_SPECIFIED_WARNING % values, stacklevel=2)
        else:
            if kwargs:
                warnings.warn("Keyword arguments to the BeautifulSoup constructor will be ignored. These would normally be passed into the TreeBuilder constructor, but a TreeBuilder instance was passed in as `builder`.")
                    
        self.builder = builder
        self.is_xml = builder.is_xml
        self.known_xml = self.is_xml
        self._namespaces = dict()
        self.parse_only = parse_only

        self.builder.initialize_soup(self)

        if hasattr(markup, 'read'):        # It's a file-type object.
            markup = markup.read()
        elif len(markup) <= 256 and (
                (isinstance(markup, bytes) and not b'<' in markup)
                or (isinstance(markup, str) and not '<' in markup)
        ):
            # Print out warnings for a couple beginner problems
            # involving passing non-markup to Beautiful Soup.
            # Beautiful Soup will still parse the input as markup,
            # just in case that's what the user really wants.
            if (isinstance(markup, str)
                and not os.path.supports_unicode_filenames):
                possible_filename = markup.encode("utf8")
            else:
                possible_filename = markup
            is_file = False
            try:
                is_file = os.path.exists(possible_filename)
            except Exception as e:
                # This is almost certainly a problem involving
                # characters not valid in filenames on this
                # system. Just let it go.
                pass
            if is_file:
                if isinstance(markup, str):
                    markup = markup.encode("utf8")
                warnings.warn(
                    '"%s" looks like a filename, not markup. You should'
                    ' probably open this file and pass the filehandle into'
                    ' Beautiful Soup.' % markup)
            self._check_markup_is_url(markup)

        for (self.markup, self.original_encoding, self.declared_html_encoding,
         self.contains_replacement_characters) in (
             self.builder.prepare_markup(
                 markup, from_encoding, exclude_encodings=exclude_encodings)):
            self.reset()
            try:
                self._feed()
                break
            except ParserRejectedMarkup:
                pass

        # Clear out the markup and remove the builder's circular
        # reference to this object.
        self.markup = None
        self.builder.soup = None

    def __copy__(self):
        copy = type(self)(
            self.encode('utf-8'), builder=self.builder, from_encoding='utf-8'
        )

        # Although we encoded the tree to UTF-8, that may not have
        # been the encoding of the original markup. Set the copy's
        # .original_encoding to reflect the original object's
        # .original_encoding.
        copy.original_encoding = self.original_encoding
        return copy

    def __getstate__(self):
        # Frequently a tree builder can't be pickled.
        d = dict(self.__dict__)
        if 'builder' in d and not self.builder.picklable:
            d['builder'] = None
        return d

    @staticmethod
    def _check_markup_is_url(markup):
        """ 
        Check if markup looks like it's actually a url and raise a warning 
        if so. Markup can be unicode or str (py2) / bytes (py3).
        """
        if isinstance(markup, bytes):
            space = b' '
            cant_start_with = (b"http:", b"https:")
        elif isinstance(markup, str):
            space = ' '
            cant_start_with = ("http:", "https:")
        else:
            return

        if any(markup.startswith(prefix) for prefix in cant_start_with):
            if not space in markup:
                if isinstance(markup, bytes):
                    decoded_markup = markup.decode('utf-8', 'replace')
                else:
                    decoded_markup = markup
                warnings.warn(
                    '"%s" looks like a URL. Beautiful Soup is not an'
                    ' HTTP client. You should probably use an HTTP client like'
                    ' requests to get the document behind the URL, and feed'
                    ' that document to Beautiful Soup.' % decoded_markup
                )

    def _feed(self):
        # Convert the document to Unicode.
        self.builder.reset()

        self.builder.feed(self.markup)
        # Close out any unfinished strings and close all the open tags.
        self.endData()
        while self.currentTag.name != self.ROOT_TAG_NAME:
            self.popTag()

    def reset(self):
        Tag.__init__(self, self, self.builder, self.ROOT_TAG_NAME)
        self.hidden = 1
        self.builder.reset()
        self.current_data = []
        self.currentTag = None
        self.tagStack = []
        self.preserve_whitespace_tag_stack = []
        self.pushTag(self)

    def new_tag(self, name, namespace=None, nsprefix=None, attrs={}, **kwattrs):
        """Create a new tag associated with this soup."""
        kwattrs.update(attrs)
        return Tag(None, self.builder, name, namespace, nsprefix, kwattrs)

    def new_string(self, s, subclass=NavigableString):
        """Create a new NavigableString associated with this soup."""
        return subclass(s)

    def insert_before(self, successor):
        raise NotImplementedError("BeautifulSoup objects don't support insert_before().")

    def insert_after(self, successor):
        raise NotImplementedError("BeautifulSoup objects don't support insert_after().")

    def popTag(self):
        tag = self.tagStack.pop()
        if self.preserve_whitespace_tag_stack and tag == self.preserve_whitespace_tag_stack[-1]:
            self.preserve_whitespace_tag_stack.pop()
        #print "Pop", tag.name
        if self.tagStack:
            self.currentTag = self.tagStack[-1]
        return self.currentTag

    def pushTag(self, tag):
        #print "Push", tag.name
        if self.currentTag is not None:
            self.currentTag.contents.append(tag)
        self.tagStack.append(tag)
        self.currentTag = self.tagStack[-1]
        if tag.name in self.builder.preserve_whitespace_tags:
            self.preserve_whitespace_tag_stack.append(tag)

    def endData(self, containerClass=NavigableString):
        if self.current_data:
            current_data = ''.join(self.current_data)
            # If whitespace is not preserved, and this string contains
            # nothing but ASCII spaces, replace it with a single space
            # or newline.
            if not self.preserve_whitespace_tag_stack:
                strippable = True
                for i in current_data:
                    if i not in self.ASCII_SPACES:
                        strippable = False
                        break
                if strippable:
                    if '\n' in current_data:
                        current_data = '\n'
                    else:
                        current_data = ' '

            # Reset the data collector.
            self.current_data = []

            # Should we add this string to the tree at all?
            if self.parse_only and len(self.tagStack) <= 1 and \
                   (not self.parse_only.text or \
                    not self.parse_only.search(current_data)):
                return

            o = containerClass(current_data)
            self.object_was_parsed(o)

    def object_was_parsed(self, o, parent=None, most_recent_element=None):
        """Add an object to the parse tree."""
        if parent is None:
            parent = self.currentTag
        if most_recent_element is not None:
            previous_element = most_recent_element
        else:
            previous_element = self._most_recent_element

        next_element = previous_sibling = next_sibling = None
        if isinstance(o, Tag):
            next_element = o.next_element
            next_sibling = o.next_sibling
            previous_sibling = o.previous_sibling
            if previous_element is None:
                previous_element = o.previous_element

        fix = parent.next_element is not None

        o.setup(parent, previous_element, next_element, previous_sibling, next_sibling)

        self._most_recent_element = o
        parent.contents.append(o)

        # Check if we are inserting into an already parsed node.
        if fix:
            self._linkage_fixer(parent)

    def _linkage_fixer(self, el):
        """Make sure linkage of this fragment is sound."""

        first = el.contents[0]
        child = el.contents[-1]
        descendant = child

        if child is first and el.parent is not None:
            # Parent should be linked to first child
            el.next_element = child
            # We are no longer linked to whatever this element is
            prev_el = child.previous_element
            if prev_el is not None and prev_el is not el:
                prev_el.next_element = None
            # First child should be linked to the parent, and no previous siblings.
            child.previous_element = el
            child.previous_sibling = None

        # We have no sibling as we've been appended as the last.
        child.next_sibling = None

        # This index is a tag, dig deeper for a "last descendant"
        if isinstance(child, Tag) and child.contents:
            descendant = child._last_descendant(False)

        # As the final step, link last descendant. It should be linked
        # to the parent's next sibling (if found), else walk up the chain
        # and find a parent with a sibling. It should have no next sibling.
        descendant.next_element = None
        descendant.next_sibling = None
        target = el
        while True:
            if target is None:
                break
            elif target.next_sibling is not None:
                descendant.next_element = target.next_sibling
                target.next_sibling.previous_element = child
                break
            target = target.parent

    def _popToTag(self, name, nsprefix=None, inclusivePop=True):
        """Pops the tag stack up to and including the most recent
        instance of the given tag. If inclusivePop is false, pops the tag
        stack up to but *not* including the most recent instqance of
        the given tag."""
        #print "Popping to %s" % name
        if name == self.ROOT_TAG_NAME:
            # The BeautifulSoup object itself can never be popped.
            return

        most_recently_popped = None

        stack_size = len(self.tagStack)
        for i in range(stack_size - 1, 0, -1):
            t = self.tagStack[i]
            if (name == t.name and nsprefix == t.prefix):
                if inclusivePop:
                    most_recently_popped = self.popTag()
                break
            most_recently_popped = self.popTag()

        return most_recently_popped

    def handle_starttag(self, name, namespace, nsprefix, attrs):
        """Push a start tag on to the stack.

        If this method returns None, the tag was rejected by the
        SoupStrainer. You should proceed as if the tag had not occurred
        in the document. For instance, if this was a self-closing tag,
        don't call handle_endtag.
        """

        # print "Start tag %s: %s" % (name, attrs)
        self.endData()

        if (self.parse_only and len(self.tagStack) <= 1
            and (self.parse_only.text
                 or not self.parse_only.search_tag(name, attrs))):
            return None

        tag = Tag(self, self.builder, name, namespace, nsprefix, attrs,
                  self.currentTag, self._most_recent_element)
        if tag is None:
            return tag
        if self._most_recent_element is not None:
            self._most_recent_element.next_element = tag
        self._most_recent_element = tag
        self.pushTag(tag)
        return tag

    def handle_endtag(self, name, nsprefix=None):
        #print "End tag: " + name
        self.endData()
        self._popToTag(name, nsprefix)

    def handle_data(self, data):
        self.current_data.append(data)

    def decode(self, pretty_print=False,
               eventual_encoding=DEFAULT_OUTPUT_ENCODING,
               formatter="minimal"):
        """Returns a string or Unicode representation of this document.
        To get Unicode, pass None for encoding."""

        if self.is_xml:
            # Print the XML declaration
            encoding_part = ''
            if eventual_encoding != None:
                encoding_part = ' encoding="%s"' % eventual_encoding
            prefix = '<?xml version="1.0"%s?>\n' % encoding_part
        else:
            prefix = ''
        if not pretty_print:
            indent_level = None
        else:
            indent_level = 0
        return prefix + super(BeautifulSoup, self).decode(
            indent_level, eventual_encoding, formatter)

# Alias to make it easier to type import: 'from bs4 import _soup'
_s = BeautifulSoup
_soup = BeautifulSoup

class BeautifulStoneSoup(BeautifulSoup):
    """Deprecated interface to an XML parser."""

    def __init__(self, *args, **kwargs):
        kwargs['features'] = 'xml'
        warnings.warn(
            'The BeautifulStoneSoup class is deprecated. Instead of using '
            'it, pass features="xml" into the BeautifulSoup constructor.')
        super(BeautifulStoneSoup, self).__init__(*args, **kwargs)


class StopParsing(Exception):
    pass

class FeatureNotFound(ValueError):
    pass


#By default, act as an HTML pretty-printer.
if __name__ == '__main__':
    import sys
    soup = BeautifulSoup(sys.stdin)
    print(soup.prettify())
