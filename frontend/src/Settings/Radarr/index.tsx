import React, { FunctionComponent } from "react";
import { Container } from "react-bootstrap";
import { connect } from "react-redux";

import {
  Check,
  Group,
  Input,
  Message,
  Slider,
  Text,
  CollapseBox,
  TestUrlButton,
  TestUrl,
} from "../components";

import SettingTemplate from "../components/template";

interface Props {}

function buildUrl(settings: SystemSettings, change: LooseObject): TestUrl {
  let url: TestUrl = {
    address: settings.radarr.ip,
    port: settings.radarr.port.toString(),
    url: settings.radarr.base_url ?? "/",
    apikey: settings.radarr.apikey,
    ssl: settings.radarr.ssl,
  };

  if ("settings-radarr-ip" in change) {
    url.address = change["settings-radarr-ip"];
  }

  if ("settings-radarr-port" in change) {
    url.port = change["settings-radarr-port"];
  }

  if ("settings-radarr-base_url" in change) {
    url.url = change["settings-radarr-base_url"];
  }

  if ("settings-radarr-apikey" in change) {
    url.apikey = change["settings-radarr-apikey"];
  }

  if ("settings-radarr-ssl" in change) {
    url.ssl = change["settings-radarr-ssl"];
  }

  return url;
}

const SettingsRadarrView: FunctionComponent<Props> = () => (
  <SettingTemplate title="Radarr - Bazarr (Settings)">
    {(settings, update, change) => (
      <Container>
        <CollapseBox
          defaultOpen={settings.general.use_radarr}
          control={(change) => (
            <Group header="Use Radarr">
              <Input>
                <Check
                  label="Enabled"
                  defaultValue={settings.general.use_radarr}
                  onChange={(v) => {
                    change(v);
                    update(v, "settings-general-use_radarr");
                  }}
                ></Check>
              </Input>
            </Group>
          )}
        >
          <Group header="Host">
            <Input name="Address">
              <Text
                defaultValue={settings.radarr.ip}
                onChange={(v) => update(v, "settings-radarr-ip")}
              ></Text>
              <Message type="info">Hostname or IPv4 Address</Message>
            </Input>
            <Input name="Port">
              <Text
                defaultValue={settings.radarr.port}
                onChange={(v) => update(v, "settings-radarr-port")}
              ></Text>
            </Input>
            <Input name="Base URL">
              <Text
                prefix="/"
                defaultValue={settings.radarr.base_url?.slice(1)}
                onChange={(v) => update("/" + v, "settings-radarr-base_url")}
              ></Text>
            </Input>
            <Input name="API Key">
              <Text
                defaultValue={settings.radarr.apikey}
                onChange={(v) => update(v, "settings-radarr-apikey")}
              ></Text>
            </Input>
            <Input>
              <Check
                label="SSL"
                defaultValue={settings.radarr.ssl}
                onChange={(v) => update(v, "settings-radarr-ssl")}
              ></Check>
            </Input>
            <Input>
              <TestUrlButton url={buildUrl(settings, change)}></TestUrlButton>
            </Input>
          </Group>
          <Group header="Options">
            <Input name="Minimum Score">
              <Slider
                defaultValue={settings.general.minimum_score_movie}
                onAfterChange={(v) =>
                  update(v, "settings-general-minimum_score_movie")
                }
              ></Slider>
            </Input>
            <Input name="Excluded Tags">
              <Text
                // TODO: Currently Unusable
                disabled
                defaultValue={settings.radarr.excluded_tags.join(",")}
              ></Text>
              <Message type="info">
                Movies with those tags (case sensitive) in Radarr will be
                excluded from automatic download of subtitles.
              </Message>
            </Input>
            <Input>
              <Check
                label="Download Only Monitored"
                defaultValue={settings.radarr.only_monitored}
                onChange={(v) => update(v, "settings-radarr-only_monitored")}
              ></Check>
              <Message type="info">
                Automatic download of subtitles will only happen for monitored
                movies in Radarr.
              </Message>
            </Input>
          </Group>
        </CollapseBox>
      </Container>
    )}
  </SettingTemplate>
);

export default connect()(SettingsRadarrView);
