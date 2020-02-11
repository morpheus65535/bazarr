"""Write to stdout without causing UnicodeEncodeError
"""

import sys


if (getattr(sys.stdout, "errors", "") == "strict" and
        not getattr(sys.stdout, "encoding", "").lower().startswith("utf")):
    try:
        import translit
        sys.stdout = translit.StreamFilter(sys.stdout)
    except ImportError:
        import codecs
        import unicodedata
        import warnings

        TRANSLIT_MAP = {
            0x2018: "'",
            0x2019: "'",
            0x201c: '"',
            0x201d: '"',
        }

        def simplify(s):
            s = s.translate(TRANSLIT_MAP)
            return "".join([c for c in unicodedata.normalize("NFKD", s)
                            if not unicodedata.combining(c)])

        def simple_translit_error_handler(error):
            if not isinstance(error, UnicodeEncodeError):
                raise error
            chunk = error.object[error.start:error.end]
            repl = simplify(chunk)
            repl = (repl.encode(error.encoding, "backslashreplace")
                    .decode(error.encoding))
            return repl, error.end

        class SimpleTranslitStreamFilter:
            """Filter a stream through simple transliteration.
            """
            errors = "simple_translit"

            def __init__(self, target):
                self.target = target

            def __getattr__(self, name):
                return getattr(self.target, name)

            def write(self, s):
                self.target.write(self.downgrade(s))

            def writelines(self, lines):
                self.target.writelines(
                    [self.downgrade(line) for line in lines])

            def downgrade(self, s):
                return (s.encode(self.target.encoding, self.errors)
                        .decode(self.target.encoding))

        codecs.register_error(SimpleTranslitStreamFilter.errors,
                              simple_translit_error_handler)
        sys.stdout = SimpleTranslitStreamFilter(sys.stdout)
        warnings.warn("translit is unavailable", ImportWarning)
