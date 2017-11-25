BEGIN TRANSACTION;
CREATE TABLE "table_shows" (
	`tvdbId`	INTEGER NOT NULL UNIQUE,
	`title`	TEXT NOT NULL,
	`path`	TEXT NOT NULL UNIQUE,
	`languages`	TEXT,
	`hearing_impaired`	TEXT,
	`sonarrSeriesId`	INTEGER NOT NULL UNIQUE,
	`overview`	TEXT,
	`poster`	TEXT,
	`fanart`	TEXT,
	PRIMARY KEY(`tvdbId`)
);
CREATE TABLE "table_settings_sonarr" (
	`ip`	TEXT NOT NULL,
	`port`	INTEGER NOT NULL,
	`base_url`	TEXT,
	`ssl`	INTEGER,
	`apikey`	TEXT
);
INSERT INTO `table_settings_sonarr` (ip,port,base_url,ssl,apikey) VALUES ('127.0.0.1',8989,'/','False',Null);
CREATE TABLE "table_settings_providers" (
	`name`	TEXT NOT NULL UNIQUE,
	`enabled`	INTEGER,
	PRIMARY KEY(`name`)
);
CREATE TABLE "table_settings_languages" (
	`code3`	TEXT NOT NULL UNIQUE,
	`code2`	TEXT,
	`name`	TEXT NOT NULL,
	`enabled`	INTEGER,
	PRIMARY KEY(`code3`)
);
CREATE TABLE "table_settings_general" (
	`ip`	TEXT NOT NULL,
	`port`	INTEGER NOT NULL,
	`base_url`	TEXT,
	`path_mapping`	TEXT,
	`log_level`	TEXT,
	`branch`	TEXT,
	`auto_update`	INTEGER
);
INSERT INTO `table_settings_general` (ip,port,base_url,path_mapping,log_level, branch, auto_update) VALUES ('0.0.0.0',6767,'/',Null,'INFO','master','True');
CREATE TABLE "table_history" (
	`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	`action`	INTEGER NOT NULL,
	`sonarrSeriesId`	INTEGER NOT NULL,
	`sonarrEpisodeId`	INTEGER NOT NULL,
	`timestamp`	INTEGER NOT NULL,
	`description`	TEXT NOT NULL
);
CREATE TABLE "table_episodes" (
	`sonarrSeriesId`	INTEGER NOT NULL,
	`sonarrEpisodeId`	INTEGER NOT NULL UNIQUE,
	`title`	TEXT NOT NULL,
	`path`	TEXT NOT NULL UNIQUE,
	`season`	INTEGER NOT NULL,
	`episode`	INTEGER NOT NULL,
	`subtitles`	TEXT,
	`missing_subtitles`	TEXT
);
COMMIT;
