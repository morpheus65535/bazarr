"""
tencent translator API
"""

__copyright__ = "Copyright (C) 2020 Nidhal Baccouri"

import base64
import hashlib
import hmac
import os
import time
from typing import List, Optional

import requests

from deep_translator.base import BaseTranslator
from deep_translator.constants import (
    BASE_URLS,
    TENCENT_LANGUAGE_TO_CODE,
    TENCENT_SECRET_ID_ENV_VAR,
    TENCENT_SECRET_KEY_ENV_VAR,
)
from deep_translator.exceptions import (
    ApiKeyException,
    ServerException,
    TencentAPIerror,
    TranslationNotFound,
)
from deep_translator.validate import is_empty, is_input_valid


class TencentTranslator(BaseTranslator):
    """
    class that wraps functions, which use the TentCentTranslator translator
    under the hood to translate word(s)
    """

    def __init__(
        self,
        source: str = "en",
        target: str = "zh",
        secret_id: Optional[str] = os.getenv(TENCENT_SECRET_ID_ENV_VAR, None),
        secret_key: Optional[str] = os.getenv(
            TENCENT_SECRET_KEY_ENV_VAR, None
        ),
        **kwargs
    ):
        """
        @param secret_id: your tencent cloud api secret id.
        Get one here: https://console.cloud.tencent.com/capi
        @param secret_key: your tencent cloud api secret key.
        @param source: source language
        @param target: target language
        """
        if not secret_id:
            raise ApiKeyException(env_var=TENCENT_SECRET_ID_ENV_VAR)

        if not secret_key:
            raise ApiKeyException(env_var=TENCENT_SECRET_KEY_ENV_VAR)

        self.secret_id = secret_id
        self.secret_key = secret_key
        url = BASE_URLS.get("TENENT")
        super().__init__(
            base_url=url,
            source=source,
            target=target,
            languages=TENCENT_LANGUAGE_TO_CODE,
            **kwargs
        )

    def translate(self, text: str, **kwargs) -> str:
        """
        @param text: text to translate
        @return: translated text
        """
        if is_input_valid(text):
            if self._same_source_target() or is_empty(text):
                return text

            # Create the request parameters.
            translate_endpoint = self._base_url.replace("https://", "")
            params = {
                "Action": "TextTranslate",
                "Nonce": 11886,
                "ProjectId": 0,
                "Region": "ap-guangzhou",
                "SecretId": self.secret_id,
                "Source": self.source,
                "SourceText": text,
                "Target": self.target,
                "Timestamp": int(time.time()),
                "Version": "2018-03-21",
            }
            s = "GET" + translate_endpoint + "/?"
            query_str = "&".join(
                "%s=%s" % (k, params[k]) for k in sorted(params)
            )
            hmac_str = hmac.new(
                self.secret_key.encode("utf8"),
                (s + query_str).encode("utf8"),
                hashlib.sha1,
            ).digest()
            params["Signature"] = base64.b64encode(hmac_str)

            # Do the request and check the connection.
            try:
                response = requests.get(self._base_url, params=params)
            except ConnectionError:
                raise ServerException(503)
            # If the answer is not success, raise server exception.
            if response.status_code != 200:
                raise ServerException(response.status_code)
            # Get the response and check is not empty.
            res = response.json()
            if not res:
                raise TranslationNotFound(text)
            # Process and return the response.
            if "Error" in res["Response"]:
                raise TencentAPIerror(res["Response"]["Error"]["Code"])
            return res["Response"]["TargetText"]

    def translate_file(self, path: str, **kwargs) -> str:
        return self._translate_file(path, **kwargs)

    def translate_batch(self, batch: List[str], **kwargs) -> List[str]:
        """
        @param batch: list of texts to translate
        @return: list of translations
        """
        return self._translate_batch(batch, **kwargs)
