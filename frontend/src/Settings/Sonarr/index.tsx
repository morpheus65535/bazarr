import React, { FunctionComponent, useCallback } from "react";
import { InputGroup } from "react-bootstrap";
import { seriesTypeOptions } from "./options";
import {
  Chips,
  Check,
  Group,
  Input,
  Message,
  Selector,
  Slider,
  Text,
  CollapseBox,
  URLTestButton,
  SettingsProvider,
} from "../components";

interface Props {}

const SettingsSonarrView: FunctionComponent<Props> = () => {
  const baseUrlOverride = useCallback((settings: SystemSettings) => {
    return settings.sonarr.base_url?.slice(1) ?? "";
  }, []);

  return (
    <SettingsProvider title="Sonarr - Bazarr (Settings)">
      <CollapseBox>
        <CollapseBox.Control>
          <Group header="Use Sonarr">
            <Input>
              <Check
                label="Enabled"
                settingKey="settings-general-use_sonarr"
              ></Check>
            </Input>
          </Group>
        </CollapseBox.Control>
        <CollapseBox.Content indent={false}>
          <Group header="Host">
            <Input name="Address">
              <Text settingKey="settings-sonarr-ip"></Text>
              <Message>Hostname or IPv4 Address</Message>
            </Input>
            <Input name="Port">
              <Text settingKey="settings-sonarr-port"></Text>
            </Input>
            <Input name="Base URL">
              <InputGroup>
                <InputGroup.Prepend>
                  <InputGroup.Text>/</InputGroup.Text>
                </InputGroup.Prepend>
                <Text
                  settingKey="settings-sonarr-base_url"
                  override={baseUrlOverride}
                  beforeStaged={(v) => "/" + v}
                ></Text>
              </InputGroup>
            </Input>
            <Input name="API Key">
              <Text settingKey="settings-sonarr-apikey"></Text>
            </Input>
            <Input>
              <Check label="SSL" settingKey="settings-sonarr-ssl"></Check>
            </Input>
            <Input>
              <URLTestButton category="sonarr"></URLTestButton>
            </Input>
          </Group>
          <Group header="Options">
            <Input name="Minimum Score">
              <Slider settingKey="settings-general-minimum_score"></Slider>
            </Input>
            <Input name="Excluded Tags">
              <Chips settingKey="settings-sonarr-excluded_tags"></Chips>
              <Message>
                Episodes from series with those tags (case sensitive) in Sonarr
                will be excluded from automatic download of subtitles.
              </Message>
            </Input>
            <Input name="Excluded Series Types">
              <Selector
                settingKey="settings-sonarr-excluded_series_types"
                multiple
                options={seriesTypeOptions}
              ></Selector>
              <Message>
                Episodes from series with those types in Sonarr will be excluded
                from automatic download of subtitles.
              </Message>
            </Input>
            <Input>
              <Check
                label="Download Only Monitored"
                settingKey="settings-sonarr-only_monitored"
              ></Check>
              <Message>
                Automatic download of subtitles will only happen for monitored
                episodes in Sonarr.
              </Message>
            </Input>
          </Group>
        </CollapseBox.Content>
      </CollapseBox>
    </SettingsProvider>
  );
};

export default SettingsSonarrView;
