import React, { FunctionComponent } from "react";
import { Container } from "react-bootstrap";
import { connect } from "react-redux";

import {
  Check,
  Group,
  Input,
  Message,
  Selector,
  Slider,
  Text,
  CollapseBox,
} from "../Components";

import SettingTemplate from "../Components/template";

interface Props {}

const seriesTypeOptions = {
  standard: "Standard",
  anime: "Anime",
  daily: "Daily",
};

const SettingsSonarrView: FunctionComponent<Props> = () => {
  return (
    <SettingTemplate title="Sonarr - Bazarr (Settings)">
      {(settings, update) => (
        <Container className="p-4">
          <CollapseBox
            defaultOpen={settings.general.use_sonarr}
            control={(change) => (
              <Group header="Use Sonarr">
                <Input>
                  <Check
                    label="Enabled"
                    remoteKey="settings-general-use_sonarr"
                    defaultValue={settings.general.use_sonarr}
                    onChange={(v, k) => {
                      change(v);
                      update(v, k);
                    }}
                  ></Check>
                </Input>
              </Group>
            )}
          >
            <Group header="Host">
              <Input name="Address">
                <Text
                  remoteKey="settings-sonarr-ip"
                  defaultValue={settings.sonarr.ip}
                  onChange={update}
                ></Text>
                <Message type="info">Hostname or IPv4 Address</Message>
              </Input>
              <Input name="Port">
                <Text
                  remoteKey="settings-sonarr-port"
                  defaultValue={settings.sonarr.port}
                  onChange={update}
                ></Text>
              </Input>
              <Input name="Base URL">
                <Text
                  prefix="/"
                  remoteKey="settings-sonarr-base_url"
                  defaultValue={settings.sonarr.base_url}
                  onChange={update}
                ></Text>
              </Input>
              <Input name="API Key">
                <Text
                  remoteKey="settings-sonarr-apikey"
                  defaultValue={settings.sonarr.apikey}
                  onChange={update}
                ></Text>
              </Input>
              <Input>
                <Check
                  label="SSL"
                  remoteKey="settings-sonarr-ssl"
                  defaultValue={settings.sonarr.ssl}
                  onChange={update}
                ></Check>
              </Input>
            </Group>
            <Group header="Options">
              <Input name="Minimum Score">
                <Slider></Slider>
              </Input>
              <Input name="Excluded Tags">
                <Text
                  // TODO: Currently Unusable
                  disabled
                  defaultValue={settings.sonarr.excluded_tags.join(",")}
                ></Text>
                <Message type="info">
                  Episodes from series with those tags (case sensitive) in
                  Sonarr will be excluded from automatic download of subtitles.
                </Message>
              </Input>
              <Input name="Excluded Series Types">
                <Selector
                  // TODO: Bug occure when only select single value
                  multiply={true}
                  options={seriesTypeOptions}
                  defaultKey={settings.sonarr.excluded_series_types}
                  onSelect={(v) =>
                    update(v, "settings-sonarr-excluded_series_types")
                  }
                ></Selector>
                <Message type="info">
                  Episodes from series with those types in Sonarr will be
                  excluded from automatic download of subtitles.
                </Message>
              </Input>
              <Input>
                <Check
                  label="Download Only Monitored"
                  remoteKey="settings-sonarr-only_monitored"
                  defaultValue={settings.sonarr.only_monitored}
                  onChange={update}
                ></Check>
                <Message type="info">
                  Automatic download of subtitles will only happen for monitored
                  episodes in Sonarr.
                </Message>
              </Input>
            </Group>
          </CollapseBox>
        </Container>
      )}
    </SettingTemplate>
  );
};

export default connect()(SettingsSonarrView);
