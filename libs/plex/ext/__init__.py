from plex.core.extension import ExtensionImporter

importer = ExtensionImporter(['plex_%s'], __name__)
importer.install()
