
class BaseParser:
    @classmethod
    def parse(cls, data, rawMode, includeMissing):
        """Core of the parser classes
        
        Collects all methods prefixed with "value_" and builds a dict of 
        their return values. Parser classes will inherit from this class.
        All methods that begin with "value_" in a parser class will be given
        the same `data` argument and are expected to pull their corresponding
        value from the collection.

        These methods return a tuple - their raw value and formatted value.
        The raw value is a string or tuple of string and the formatted value
        be of type string, int, float, or tuple.
        
        If no data is found in a method, the raw value is expected to be None,
        and for the formatted value, strings will be "null", ints will be 0, 
        floats will be 0.0.

        Args:
            data (dict): Raw video data 
            rawMode (bool): Returns raw values instead of formatted values
            includeMissing (bool): If value is missing, return "empty" value

        Returns:
            dict<str, dict<str, var>>: Parsed data from class methods, may not have every value.

        """
        parsers = [getattr(cls, p) for p in dir(cls) if p.startswith("value_")]
        info = {}
        for parser in parsers:
            parsed_raw, parsed_formatted = parser(data)
            if parsed_raw == None and not includeMissing:
                continue
            name = parser.__name__[6:]
            if rawMode:
                info[name] = parsed_raw
            else:
                info[name] = parsed_formatted
        return info
