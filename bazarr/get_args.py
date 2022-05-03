# coding=utf-8

# This is required to prevent daemon (bazarr.py) from raising an ImportError Exception after upgrading from 1.0.4
from .app.get_args import args  # noqa: W0611
