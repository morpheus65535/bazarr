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
  TestUrlButton,
  TestUrl,
} from "../Components";

import SettingTemplate from "../Components/template";

interface Props {}

const seriesTypeOptions = {
  standard: "Standard",
  anime: "Anime",
  daily: "Daily",
};

function buildUrl(settings: SystemSettings, change: LooseObject): TestUrl {
  let url: TestUrl = {
    address: settings.sonarr.ip,
    port: settings.sonarr.port.toString(),
    url: settings.sonarr.base_url ?? "/",
    apikey: settings.sonarr.apikey,
    ssl: settings.sonarr.ssl,
  };

  if ("settings-sonarr-ip" in change) {
    url.address = change["settings-sonarr-ip"];
  }

  if ("settings-sonarr-port" in change) {
    url.port = change["settings-sonarr-port"];
  }

  if ("settings-sonarr-base_url" in change) {
    url.url = change["settings-sonarr-base_url"];
  }

  if ("settings-sonarr-apikey" in change) {
    url.apikey = change["settings-sonarr-apikey"];
  }

  if ("settings-sonarr-ssl" in change) {
    url.ssl = change["settings-sonarr-ssl"];
  }

  return url;
}

const SettingsSonarrView: FunctionComponent<Props> = () => (
  <SettingTemplate title="Sonarr - Bazarr (Settings)">
    {(settings, update, change) => (
      <Container>
        <CollapseBox
          defaultOpen={settings.general.use_sonarr}
          control={(change) => (
            <Group header="Use Sonarr">
              <Input>
                <Check
                  label="Enabled"
                  defaultValue={settings.general.use_sonarr}
                  onChange={(v) => {
                    change(v);
                    update(v, "settings-general-use_sonarr");
                  }}
                ></Check>
              </Input>
            </Group>
          )}
        >
          <Group header="Host">
            <Input name="Address">
              <Text
                defaultValue={settings.sonarr.ip}
                onChange={(v) => update(v, "settings-sonarr-ip")}
              ></Text>
              <Message type="info">Hostname or IPv4 Address</Message>
            </Input>
            <Input name="Port">
              <Text
                defaultValue={settings.sonarr.port}
                onChange={(v) => update(v, "settings-sonarr-port")}
              ></Text>
            </Input>
            <Input name="Base URL">
              <Text
                prefix="/"
                defaultValue={settings.sonarr.base_url}
                onChange={(v) => update(v, "settings-sonarr-base_url")}
              ></Text>
            </Input>
            <Input name="API Key">
              <Text
                defaultValue={settings.sonarr.apikey}
                onChange={(v) => update(v, "settings-sonarr-apikey")}
              ></Text>
            </Input>
            <Input>
              <Check
                label="SSL"
                defaultValue={settings.sonarr.ssl}
                onChange={(v) => update(v, "settings-sonarr-ssl")}
              ></Check>
            </Input>
            <Input>
              <TestUrlButton url={buildUrl(settings, change)}></TestUrlButton>
            </Input>
          </Group>
          <Group header="Options">
            <Input name="Minimum Score">
              <Slider
                defaultValue={settings.general.minimum_score}
                onAfterChange={(v) =>
                  update(v, "settings-general-minimum_score")
                }
              ></Slider>
            </Input>
            <Input name="Excluded Tags">
              <Text
                // TODO: Currently Unusable
                disabled
                defaultValue={settings.sonarr.excluded_tags.join(",")}
              ></Text>
              <Message type="info">
                Episodes from series with those tags (case sensitive) in Sonarr
                will be excluded from automatic download of subtitles.
              </Message>
            </Input>
            <Input name="Excluded Series Types">
              <Selector
                // TODO: Bug occure when only select single value
                multiply={true}
                options={seriesTypeOptions}
                defaultKey={settings.sonarr.excluded_series_types}
                onMultiSelect={(v) =>
                  update(v, "settings-sonarr-excluded_series_types")
                }
              ></Selector>
              <Message type="info">
                Episodes from series with those types in Sonarr will be excluded
                from automatic download of subtitles.
              </Message>
            </Input>
            <Input>
              <Check
                label="Download Only Monitored"
                defaultValue={settings.sonarr.only_monitored}
                onChange={(v) => update(v, "settings-sonarr-only_monitored")}
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

export default connect()(SettingsSonarrView);
