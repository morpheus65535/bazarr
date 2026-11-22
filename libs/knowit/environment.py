"""Collect untruncated environment information used by bug reports."""

import glob
import locale
import os
import platform
import sys
import sysconfig
import typing

import knowit

#: Environment variables that change how paths and text are decoded.
RELEVANT_ENV_VARS = (
    'LANG',
    'LC_ALL',
    'LC_CTYPE',
    'PYTHONUTF8',
    'PYTHONIOENCODING',
    'PYTHONLEGACYWINDOWSFSENCODING',
)

Section = dict[str, typing.Any]
Environment = dict[str, Section]


def _package_dir() -> str:
    package_file = getattr(knowit, '__file__', None)
    return os.path.dirname(os.path.abspath(package_file)) if package_file else ''


def detect_installation(package_dir: str | None = None) -> str:
    """Tell apart a regular install from a source checkout or a vendored copy.

    Applications such as Bazarr and Medusa bundle knowit inside their own tree. Those
    copies are frequently several releases behind, which is worth knowing before
    investigating a traceback.
    """
    package_dir = package_dir if package_dir is not None else _package_dir()
    if not package_dir:
        return 'unknown'

    parent = os.path.dirname(package_dir)
    paths = sysconfig.get_paths()
    site_dirs = [paths[key] for key in ('purelib', 'platlib') if paths.get(key)]
    if any(os.path.normcase(parent) == os.path.normcase(site_dir) for site_dir in site_dirs):
        return 'site-packages'

    if any(os.path.isfile(os.path.join(parent, name)) for name in ('pyproject.toml', 'setup.py', 'setup.cfg')):
        return 'source checkout'

    return 'vendored (bundled by another application)'


def detect_libc() -> str | None:
    """Return the C library flavour, which differs between Debian-like and Alpine images."""
    name, version = platform.libc_ver()
    if name:
        return f'{name} {version}'.strip()
    if sys.platform.startswith('linux') and glob.glob('/lib/ld-musl-*'):
        return 'musl'
    return None


def detect_container() -> str | None:
    """Return the container runtime knowit seems to run in, if any."""
    if os.path.exists('/.dockerenv'):
        return 'docker'
    if os.path.exists('/run/.containerenv'):
        return 'podman'

    try:
        with open('/proc/1/cgroup', encoding='utf-8', errors='replace') as stream:
            cgroups = stream.read()
    except OSError:
        return None

    for marker in ('docker', 'containerd', 'kubepods', 'podman', 'lxc'):
        if marker in cgroups:
            return marker
    return None


def collect_knowit() -> Section:
    """Return knowit version and where it was loaded from."""
    package_dir = _package_dir()
    return {
        'version': knowit.__version__,
        'location': package_dir or 'unknown',
        'installation': detect_installation(package_dir),
    }


def collect_python() -> Section:
    """Return interpreter and operating system information."""
    section: Section = {
        'version': platform.python_version(),
        'implementation': platform.python_implementation(),
        'executable': sys.executable,
        'platform': sys.platform,
        'platform_details': platform.platform(),
        'machine': platform.machine(),
    }
    libc = detect_libc()
    if libc:
        section['libc'] = libc
    container = detect_container()
    if container:
        section['container'] = container
    return section


def collect_locale() -> Section:
    """Return the encodings that decide how non-ascii paths are handled."""
    section: Section = {
        'filesystem_encoding': sys.getfilesystemencoding(),
        'filesystem_errors': sys.getfilesystemencodeerrors(),
        'default_encoding': sys.getdefaultencoding(),
        'preferred_encoding': locale.getpreferredencoding(False),
        'stdout_encoding': getattr(sys.stdout, 'encoding', None) or 'unknown',
    }
    for name in RELEVANT_ENV_VARS:
        section[name] = os.environ.get(name, '<unset>')
    return section


def collect_providers(context: typing.Mapping[str, typing.Any] | None = None) -> Section:
    """Return the resolved location and version of every backend."""
    from knowit import api

    section: Section = {}
    for name, versions in api.dependencies(context).items():
        if versions:
            section[name] = {location or 'unknown': version for location, version in versions.items()}
        else:
            section[name] = 'not found'
    return section


def collect_environment(context: typing.Mapping[str, typing.Any] | None = None) -> Environment:
    """Return every environment section, with no value truncated."""
    return {
        'knowit': collect_knowit(),
        'python': collect_python(),
        'locale': collect_locale(),
        'providers': collect_providers(context),
    }


def format_section(name: str, section: Section, indent: str = '  ') -> list[str]:
    lines = [f'{name}:']
    for key, value in section.items():
        if isinstance(value, dict):
            lines.append(f'{indent}{key}:')
            for sub_key, sub_value in value.items():
                lines.append(f'{indent * 2}{sub_key}: {sub_value}')
        else:
            lines.append(f'{indent}{key}: {value}')
    return lines


def format_environment(environment: Environment) -> str:
    """Render the environment as plain, untruncated text."""
    lines: list[str] = []
    for name, section in environment.items():
        if lines:
            lines.append('')
        lines.extend(format_section(name, section))
    return '\n'.join(lines)
