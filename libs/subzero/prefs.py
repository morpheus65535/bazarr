# coding=utf-8
import traceback
from constants import PLUGIN_IDENTIFIER


def get_user_prefs(Prefs, Logger):
    """
    loads all user prefs regardless of whether they exist in DefaultPrefs or not
    :param Prefs:
    :param Logger:
    :return:
    """

    try:
        prefs_set = Prefs._sandbox.preferences._sets[PLUGIN_IDENTIFIER]
    except:
        Logger.Error("Loading user prefs failed: %s", traceback.format_exc())
        return {}

    user_prefs = {}
    try:
        xml_path = prefs_set._user_file_path
        if not Prefs._core.storage.file_exists(xml_path):
            return {}
        prefs_str = Prefs._core.storage.load(xml_path, mtime_key=prefs_set)
        prefs_xml = Prefs._core.data.xml.from_string(prefs_str)
        for el in prefs_xml:
            user_prefs[str(el.tag)] = str(el.text)
    except:
        Logger.Error("Loading user prefs failed: %s", traceback.format_exc())
    else:
        return user_prefs
    return {}


def update_user_prefs(update_prefs, Prefs, Logger):
    prefs_set = Prefs._sandbox.preferences._sets[PLUGIN_IDENTIFIER]
    prefs_set.update_user_values(**update_prefs)
    Logger.Info("User prefs updated")
