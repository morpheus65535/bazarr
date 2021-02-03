"""
configuration object that holds data about the language detection api
"""

config = {
    "url": 'https://ws.detectlanguage.com/0.2/detect',
    "headers": {
        'User-Agent': 'Detect Language API Python Client 1.4.0',
        'Authorization': 'Bearer {}',
    }
}
