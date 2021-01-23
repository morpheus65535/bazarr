import React, { FunctionComponent, useMemo } from "react";

import SettingsTemplate from "../components/template";

import { Group, Selector, Input, SelectionBox } from "../components";
import { Container } from "react-bootstrap";

const seriesSyncOptions = {
  "1": "1 Minute",
  "5": "5 Minutes",
  "15": "15 Minutes",
  "60": "1 Hour",
  "180": "3 Hours",
};

const episodesSyncOptions = {
  "5": "5 Minutes",
  "15": "15 Minutes",
  "60": "1 Hour",
  "180": "3 Hours",
  "360": "6 Hours",
};

const moviesSyncOptions = episodesSyncOptions;

const diskUpdateOptions = {
  Manually: "Manually",
  Daily: "Daily",
  Weekly: "Weekly",
};

const dayOptions = {
  "0": "Monday",
  "1": "Tuesday",
  "2": "Wednesday",
  "3": "Thursday",
  "4": "Friday",
  "5": "Saturday",
  "6": "Sunday",
};

const upgradeOptions = {
  "3": "3 Hours",
  "6": "6 Hours",
  "12": "12 Hours",
  "24": "24 Hours",
};

interface Props {}

const SettingsSchedularView: FunctionComponent<Props> = () => {
  const timeOptions = useMemo(() => {
    let object: LooseObject = {};
    Array(24)
      .fill(undefined)
      .map((_, idx) => (object[idx.toString()] = `${idx}:00`));
    return object;
  }, []);

  return (
    <SettingsTemplate title="Schedular - Bazarr (Settings)">
      {(settings, update) => (
        <Container fluid>
          <Group header="Sonarr/Radarr Sync">
            <Input name="Update Series List from Sonarr">
              <Selector
                options={seriesSyncOptions}
                defaultKey={settings.sonarr.series_sync.toString()}
                onSelect={(v) => update(v, "settings-sonarr-series_sync")}
              ></Selector>
            </Input>
            <Input name="Update Episodes List from Sonarr">
              <Selector
                options={episodesSyncOptions}
                defaultKey={settings.sonarr.episodes_sync.toString()}
                onSelect={(v) => update(v, "settings-sonarr-episodes_sync")}
              ></Selector>
            </Input>
            <Input name="Update Movies List from Radarr">
              <Selector
                options={moviesSyncOptions}
                defaultKey={settings.radarr.movies_sync.toString()}
                onSelect={(v) => update(v, "settings-radarr-movies_sync")}
              ></Selector>
            </Input>
          </Group>
          <Group header="Disk Indexing">
            <SelectionBox
              indent
              defaultKey={settings.sonarr.full_update}
              control={(change) => (
                <Input name="Update all Episode Subtitles from Disk">
                  <Selector
                    options={diskUpdateOptions}
                    defaultKey={settings.sonarr.full_update}
                    onSelect={(v) => {
                      change(v);
                      update(v, "settings-sonarr-full_update");
                    }}
                  ></Selector>
                </Input>
              )}
            >
              {(k) => (
                <React.Fragment>
                  <Input name="Day of The Week" hidden={k !== "Weekly"}>
                    <Selector
                      options={dayOptions}
                      defaultKey={settings.sonarr.full_update_day.toString()}
                      onSelect={(v) => {
                        update(v, "settings-sonarr-full_update_day");
                      }}
                    ></Selector>
                  </Input>
                  <Input name="Time of The Day" hidden={k === "Manually"}>
                    <Selector
                      options={timeOptions}
                      defaultKey={settings.sonarr.full_update_hour.toString()}
                      onSelect={(v) => {
                        update(v, "settings-sonarr-full_update_hour");
                      }}
                    ></Selector>
                  </Input>
                </React.Fragment>
              )}
            </SelectionBox>
            <SelectionBox
              indent
              defaultKey={settings.radarr.full_update}
              control={(change) => (
                <Input name="Update all Movie Subtitles from Disk">
                  <Selector
                    options={diskUpdateOptions}
                    defaultKey={settings.radarr.full_update}
                    onSelect={(v) => {
                      change(v);
                      update(v, "settings-radarr-full_update");
                    }}
                  ></Selector>
                </Input>
              )}
            >
              {(k) => (
                <React.Fragment>
                  <Input name="Day of The Week" hidden={k !== "Weekly"}>
                    <Selector
                      options={dayOptions}
                      defaultKey={settings.radarr.full_update_day.toString()}
                      onSelect={(v) => {
                        update(v, "settings-radarr-full_update_day");
                      }}
                    ></Selector>
                  </Input>
                  <Input name="Time of The Day" hidden={k === "Manually"}>
                    <Selector
                      options={timeOptions}
                      defaultKey={settings.radarr.full_update_hour.toString()}
                      onSelect={(v) => {
                        update(v, "settings-radarr-full_update_hour");
                      }}
                    ></Selector>
                  </Input>
                </React.Fragment>
              )}
            </SelectionBox>
          </Group>
          <Group header="Search and Upgrade Subtitles">
            <Input name="Search for Missing Series Subtitles">
              <Selector
                options={upgradeOptions}
                defaultKey={settings.general.wanted_search_frequency.toString()}
                onSelect={(v) => {
                  update(v, "settings-radarr-wanted_search_frequency");
                }}
              ></Selector>
            </Input>
            <Input name="Search for Missing Movies Subtitles">
              <Selector
                options={upgradeOptions}
                defaultKey={settings.general.wanted_search_frequency_movie.toString()}
                onSelect={(v) => {
                  update(v, "settings-radarr-wanted_search_frequency_movie");
                }}
              ></Selector>
            </Input>
            <Input name="Upgrade Previously Downloaded Subtitles">
              <Selector
                options={upgradeOptions}
                defaultKey={settings.general.upgrade_frequency.toString()}
                onSelect={(v) => {
                  update(v, "settings-radarr-upgrade_frequency");
                }}
              ></Selector>
            </Input>
          </Group>
        </Container>
      )}
    </SettingsTemplate>
  );
};

export default SettingsSchedularView;
