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
	`audio_language`    "text",
	`sortTitle` "text",
	PRIMARY KEY(`tvdbId`)
);
CREATE TABLE "table_settings_providers" (
	`name`	TEXT NOT NULL UNIQUE,
	`enabled`	INTEGER,
	`username`	"text",
	`password`  "text",
	PRIMARY KEY(`name`)
);
CREATE TABLE "table_settings_notifier" (
	`name` TEXT,
	`url` TEXT,
	`enabled` INTEGER,
	PRIMARY KEY(`name`)
);
CREATE TABLE "table_settings_languages" (
	`code3`	TEXT NOT NULL UNIQUE,
	`code2`	TEXT,
	`name`	TEXT NOT NULL,
	`enabled`	INTEGER,
	`code3b`	TEXT,
	PRIMARY KEY(`code3`)
);
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
	`path`	TEXT NOT NULL,
	`season`	INTEGER NOT NULL,
	`episode`	INTEGER NOT NULL,
	`subtitles`	TEXT,
	`missing_subtitles`	TEXT,
	`scene_name`    TEXT,
	`monitored` TEXT,
	`failedAttempts` "text"
);
CREATE TABLE "table_movies" (
    `tmdbId` TEXT NOT NULL UNIQUE,
    `title` TEXT NOT NULL,
    `path` TEXT NOT NULL UNIQUE,
    `languages` TEXT,
    `subtitles` TEXT,
    `missing_subtitles` TEXT,
    `hearing_impaired` TEXT,
    `radarrId` INTEGER NOT NULL UNIQUE,
    `overview` TEXT,
    `poster` TEXT,
    `fanart` TEXT,
    `audio_language` "text",
    `sceneName` TEXT,
    `monitored` TEXT,
    `failedAttempts` "text",
    PRIMARY KEY(`tmdbId`)
);
CREATE TABLE "table_history_movie" (
    `id` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    `action` INTEGER NOT NULL,
    `radarrId` INTEGER NOT NULL,
    `timestamp` INTEGER NOT NULL,
    `description` TEXT NOT NULL
);
CREATE TABLE "system" (
    `configured` TEXT,
    `updated` TEXT
);
INSERT INTO `system` (configured, updated) VALUES ('0', '0');
COMMIT;
