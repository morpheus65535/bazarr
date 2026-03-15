# coding=utf-8
# Subsarr uses the same Subscene language names as Subsource.
# Registering under a separate name avoids duplicate-registration conflicts.
from subliminal_patch.converters.subsource import SubsourceConverter

SubsarrConverter = SubsourceConverter
