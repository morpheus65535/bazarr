from get_argv import config_dir

import sqlite3
import pycountry
import os

def load_language_in_db():
    # Get languages list in langs tuple
    langs = [[lang.alpha_3,lang.alpha_2,lang.name]
        for lang in pycountry.languages
        if hasattr(lang, 'alpha_2')]

    # Open database connection
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()

    # Insert languages in database table
    c.executemany('''INSERT OR IGNORE INTO table_settings_languages(code3, code2, name) VALUES(?, ?, ?)''', langs)
    c.execute('''INSERT OR IGNORE INTO table_settings_languages(code3, code2, name) VALUES(?, ?, ?)''', ('pob','pb','Brazilian Portuguese'))

    langs = [[lang.bibliographic,lang.alpha_3]
        for lang in pycountry.languages
        if hasattr(lang, 'alpha_2') and hasattr(lang, 'bibliographic')]

    # Update languages in database table
    c.executemany('''UPDATE table_settings_languages SET code3b = ? WHERE code3 = ?''', langs)

    # Commit changes to database table
    db.commit()

    # Close database connection
    db.close()

def language_from_alpha2(lang):
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    try:
        result = c.execute('''SELECT name FROM table_settings_languages WHERE code2 = ?''', (lang,)).fetchone()[0]
    except:
        result = None
    db.close()
    return result

def language_from_alpha3(lang):
    if lang == 'fre':
        lang = 'fra'
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    try:
        result = c.execute('''SELECT name FROM table_settings_languages WHERE code3 = ? OR code3b = ?''', (lang,lang)).fetchone()[0]
    except:
        result = None
    db.close()
    return result

def alpha2_from_alpha3(lang):
    if lang == 'fre':
        lang = 'fra'
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    try:
        result = c.execute('''SELECT code2 FROM table_settings_languages WHERE code3 = ? OR code3b = ?''', (lang,lang)).fetchone()[0]
    except:
        result = None
    db.close()
    return result

def alpha2_from_language(lang):
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    try:
        result = c.execute('''SELECT code2 FROM table_settings_languages WHERE name = ?''', (lang,)).fetchone()[0]
    except:
        result = None
    db.close()
    return result

def alpha3_from_alpha2(lang):
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    try:
        result = c.execute('''SELECT code3 FROM table_settings_languages WHERE code2 = ?''', (lang,)).fetchone()[0]
    except:
        result = None
    db.close()
    return result

def alpha3_from_language(lang):
    db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
    c = db.cursor()
    try:
        result = c.execute('''SELECT code3 FROM table_settings_languages WHERE name = ?''', (lang,)).fetchone()[0]
    except:
        result = None
    db.close()
    return result

if __name__ == '__main__':
    load_language_in_db()
