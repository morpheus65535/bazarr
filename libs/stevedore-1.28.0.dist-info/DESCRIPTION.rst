===========================================================
stevedore -- Manage dynamic plugins for Python applications
===========================================================

.. image:: https://img.shields.io/pypi/v/stevedore.svg
    :target: https://pypi.python.org/pypi/stevedore/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/dm/stevedore.svg
    :target: https://pypi.python.org/pypi/stevedore/
    :alt: Downloads

.. image:: http://governance.openstack.org/badges/stevedore.svg
    :target: http://governance.openstack.org/reference/tags/index.html

Python makes loading code dynamically easy, allowing you to configure
and extend your application by discovering and loading extensions
("*plugins*") at runtime. Many applications implement their own
library for doing this, using ``__import__`` or ``importlib``.
stevedore avoids creating yet another extension
mechanism by building on top of `setuptools entry points`_. The code
for managing entry points tends to be repetitive, though, so stevedore
provides manager classes for implementing common patterns for using
dynamically loaded extensions.

.. _setuptools entry points: http://setuptools.readthedocs.io/en/latest/pkg_resources.html?#entry-points

* Free software: Apache license
* Documentation: https://docs.openstack.org/stevedore/latest
* Source: https://git.openstack.org/cgit/openstack/stevedore
* Bugs: https://bugs.launchpad.net/python-stevedore



