import sqlite3
import os
import ast

# Open database connection
db = sqlite3.connect('bazarr.db')
c = db.cursor()

# Get general settings from database table
c.execute("SELECT * FROM table_settings_general")
general_settings = c.fetchone()

# Close database connection
db.close()

ip = general_settings[0]
port = general_settings[1]
base_url = general_settings[2]
if general_settings[3] is None:
   path_mappings = []
else:
   path_mappings = ast.literal_eval(general_settings[3])

def path_replace(path):
   for path_mapping in path_mappings:
      path = path.replace(path_mapping[0], path_mapping[1], 1)
      
      if '\\' in path:
         path = path.replace('/', '\\')
   
   return path

def path_replace_reverse(path):
   for path_mapping in path_mappings:
      if path.startswith('\\\\\\\\'):
         if '\\\\' in path:
            path = path.replace('\\\\', '\\')
         elif '\\' in path:
            path = path.replace('\\\\', '\\')
         
         path = path.replace(path_mapping[1], path_mapping[0], 1)
      elif path.startswith('\\\\'):
         path = path.replace(path_mapping[1], path_mapping[0], 1)

      if '\\' in path:
         path = path.replace('\\', '/')
         
   return path

#print path_replace_reverse(r'\\\\serveur\\media\\Series TV\\Vikings\\Season 03\\Vikings.S03E01.720p.HDTV.x264-KILLERS.mkv')
