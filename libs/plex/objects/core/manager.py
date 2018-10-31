import inspect
import logging
import os

log = logging.getLogger(__name__)

UNC_PREFIX = '\\\\?\\'


class ObjectManager(object):
    base_dir = None
    objects_dir = None
    objects_map = {}

    ignore_files = [
        '__init__.py'
    ]
    ignore_paths = [
        'plex\\objects\\core\\base.py',
        'plex\\objects\\core\\manager.py'
    ]

    @classmethod
    def discover(cls):
        cls.objects_dir = os.path.join(cls.base_dir, 'plex', 'objects')

        # Walk plex/objects directory
        for current, directories, files in os.walk(cls.objects_dir):

            # Iterate files, yield valid paths
            for filename in files:
                if not filename.endswith('.py'):
                    continue

                # Ensure filename is not in ignore list
                if filename in cls.ignore_files:
                    continue

                path = os.path.join(current, filename)

                # Ensure path is not in ignore list
                if not all([not path.endswith(p) for p in cls.ignore_paths]):
                    continue

                # Remove UNC prefix (if it exists)
                if path.startswith(UNC_PREFIX):
                    path = path[len(UNC_PREFIX):]

                path = os.path.relpath(path, cls.base_dir)
                name = os.path.splitext(path)[0].replace(os.path.sep, '.')

                yield path, name

    @classmethod
    def load(cls):
        for path, name in cls.discover():
            try:
                mod = __import__(name, fromlist=['*'])
            except Exception as ex:
                log.warn('Unable to import "%s" - %s', name, ex)
                continue

            # Get classes in module
            classes = [
                (key, getattr(mod, key)) for key in dir(mod)
                if not key.startswith('_')
            ]

            # Filter to module-specific classes
            classes = [
                (key, value) for (key, value) in classes
                if inspect.isclass(value) and value.__module__ == name
            ]

            yield classes

    @classmethod
    def construct(cls):
        log.debug('Loading descriptors...')

        cls.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', '..'))

        # Load modules, find descriptor classes
        for classes in cls.load():
            # Update object map
            for key, value in classes:
                cls.objects_map[key] = value

        log.debug('Loaded %s descriptors (%s)', len(cls.objects_map), ', '.join(sorted(cls.objects_map.keys())))
