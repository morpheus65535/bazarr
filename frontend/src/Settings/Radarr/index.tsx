import React, { FunctionComponent, useCallback } from "react";
import { InputGroup } from "react-bootstrap";
import {
  Chips,
  Check,
  Group,
  Input,
  Message,
  Slider,
  Text,
  CollapseBox,
  URLTestButton,
  SettingsProvider,
} from "../components";

interface Props {}

const SettingsRadarrView: FunctionComponent<Props> = () => {
  const baseUrlOverride = useCallback((settings: SystemSettings) => {
    return settings.sonarr.base_url?.slice(1) ?? "";
  }, []);

  return (
    <SettingsProvider title="Radarr - Bazarr (Settings)">
      <CollapseBox>
        <CollapseBox.Control>
          <Group header="Use Radarr">
            <Input>
              <Check
                label="Enabled"
                settingKey="settings-general-use_radarr"
              ></Check>
            </Input>
          </Group>
        </CollapseBox.Control>
        <CollapseBox.Content indent={false}>
          <Group header="Host">
            <Input name="Address">
              <Text settingKey="settings-radarr-ip"></Text>
              <Message>Hostname or IPv4 Address</Message>
            </Input>
            <Input name="Port">
              <Text settingKey="settings-radarr-port"></Text>
            </Input>
            <Input name="Base URL">
              <InputGroup>
                <InputGroup.Prepend>
                  <InputGroup.Text>/</InputGroup.Text>
                </InputGroup.Prepend>
                <Text
                  settingKey="settings-radarr-base_url"
                  override={baseUrlOverride}
                  beforeStaged={(v) => "/" + v}
                ></Text>
              </InputGroup>
            </Input>
            <Input name="API Key">
              <Text settingKey="settings-radarr-apikey"></Text>
            </Input>
            <Input>
              <Check label="SSL" settingKey="settings-radarr-ssl"></Check>
            </Input>
            <Input>
              <URLTestButton category="radarr"></URLTestButton>
            </Input>
          </Group>
          <Group header="Options">
            <Input name="Minimum Score">
              <Slider settingKey="settings-general-minimum_score_movie"></Slider>
            </Input>
            <Input name="Excluded Tags">
              <Chips settingKey="settings-radarr-excluded_tags"></Chips>
              <Message>
                Movies with those tags (case sensitive) in Radarr will be
                excluded from automatic download of subtitles.
              </Message>
            </Input>
            <Input>
              <Check
                label="Download Only Monitored"
                settingKey="settings-radarr-only_monitored"
              ></Check>
              <Message>
                Automatic download of subtitles will only happen for monitored
                movies in Radarr.
              </Message>
            </Input>
          </Group>
        </CollapseBox.Content>
      </CollapseBox>
    </SettingsProvider>
  );
};

export default SettingsRadarrView;
