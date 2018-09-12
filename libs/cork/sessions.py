import json
import base64
import hmac
from Crypto.Cipher import AES

def _strcmp(a, b):
    """Compares two strings while preventing timing attacks. Execution time
    is not affected by lenghth of common prefix on strings of the same length"""
    return not sum(0 if x==y else 1 for x, y in zip(a, b)) and len(a) == len(b)

class SecureSession(object):

    def __init__(self):

    json()
    
    


    
        
       base64.b64encode(hmac.new(tob(key), msg).digest())):
            return pickle.loads(base64.b64decode(msg))
