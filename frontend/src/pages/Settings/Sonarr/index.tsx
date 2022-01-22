import React, { FunctionComponent, useCallback } from "react";
import { InputGroup } from "react-bootstrap";
import {
  Check,
  Chips,
  CollapseBox,
  Group,
  Input,
  Message,
  PathMappingTable,
  Selector,
  SettingsProvider,
  Slider,
  Text,
  URLTestButton,
} from "../components";
import { seriesEnabledKey } from "../keys";
import { seriesTypeOptions } from "../options";

interface Props {}

const SettingsSonarrView: FunctionComponent<Props> = () => {
  const baseUrlOverride = useCallback((settings: Settings) => {
    return settings.sonarr.base_url?.slice(1) ?? "";
  }, []);

  return (
    <SettingsProvider title="Sonarr - Bazarr (Settings)">
      <CollapseBox>
        <CollapseBox.Control>
          <Group header="Use Sonarr">
            <Input>
              <Check label="Enabled" settingKey={seriesEnabledKey}></Check>
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
            <Input>
              <Check
                label="Exclude season zero (extras)"
                settingKey="settings-sonarr-exclude_season_zero"
              ></Check>
              <Message>
                Episodes from season zero (extras) from automatic download of
                subtitles.
              </Message>
            </Input>
          </Group>
          <Group header="Path Mappings">
            <PathMappingTable type="sonarr"></PathMappingTable>
          </Group>
        </CollapseBox.Content>
      </CollapseBox>
    </SettingsProvider>
  );
};

export default SettingsSonarrView;
