# coding: utf-8
"""
Do what is necessary to authenticate this tester as a Twitter "app", using
somebody's Twitter account.
"""
from __future__ import unicode_literals
import os


AUTH_TOKEN_PATH = os.path.expanduser('~/.cache/oauth/twitter_ftfy.auth')

def get_auth():
    """
    Twitter has some bizarre requirements about how to authorize an "app" to
    use its API.

    The user of the app has to log in to get a secret token. That's fine. But
    the app itself has its own "consumer secret" token. The app has to know it,
    and the user of the app has to not know it.

    This is, of course, impossible. It's equivalent to DRM. Your computer can't
    *really* make use of secret information while hiding the same information
    from you.

    The threat appears to be that, if you have this super-sekrit token, you can
    impersonate the app while doing something different. Well, of course you
    can do that, because you *have the source code* and you can change it to do
    what you want. You still have to log in as a particular user who has a
    token that's actually secret, you know.

    Even developers of closed-source applications that use the Twitter API are
    unsure what to do, for good reason. These "secrets" are not secret in any
    cryptographic sense. A bit of Googling shows that the secret tokens for
    every popular Twitter app are already posted on the Web.

    Twitter wants us to pretend this string can be kept secret, and hide this
    secret behind a fig leaf like everybody else does. So that's what we've
    done.
    """

    from twitter.oauth import OAuth
    from twitter import oauth_dance, read_token_file

    def unhide(secret):
        """
        Do something mysterious and exactly as secure as every other Twitter
        app.
        """
        return ''.join([chr(ord(c) - 0x2800) for c in secret])

    fig_leaf = '⠴⡹⠹⡩⠶⠴⡶⡅⡂⡩⡅⠳⡏⡉⡈⠰⠰⡹⡥⡶⡈⡐⡍⡂⡫⡍⡗⡬⡒⡧⡶⡣⡰⡄⡧⡸⡑⡣⠵⡓⠶⠴⡁'
    consumer_key = 'OFhyNd2Zt4Ba6gJGJXfbsw'

    if os.path.exists(AUTH_TOKEN_PATH):
        token, token_secret = read_token_file(AUTH_TOKEN_PATH)
    else:
        authdir = os.path.dirname(AUTH_TOKEN_PATH)
        if not os.path.exists(authdir):
            os.makedirs(authdir)
        token, token_secret = oauth_dance(
            app_name='ftfy-tester',
            consumer_key=consumer_key,
            consumer_secret=unhide(fig_leaf),
            token_filename=AUTH_TOKEN_PATH
        )

    return OAuth(
        token=token,
        token_secret=token_secret,
        consumer_key=consumer_key,
        consumer_secret=unhide(fig_leaf)
    )
