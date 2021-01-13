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

const SettingsRadarrView: FunctionComponent<Props> = () => (
  <SettingTemplate title="Radarr - Bazarr (Settings)">
    {(settings, update) => (
      <Container className="p-4">
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
                defaultValue={settings.radarr.base_url}
                onChange={(v) => update(v, "settings-radarr-base_url")}
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
          </Group>
          <Group header="Options">
            <Input name="Minimum Score">
              <Slider></Slider>
            </Input>
            <Input name="Excluded Tags">
              <Text
                // TODO: Currently Unusable
                disabled
                defaultValue={settings.radarr.excluded_tags.join(",")}
              ></Text>
              <Message type="info">
                Movies with those tags (case sensitive) in Radarr
                will be excluded from automatic download of subtitles.
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
