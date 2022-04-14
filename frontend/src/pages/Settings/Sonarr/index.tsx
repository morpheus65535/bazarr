import { FunctionComponent, useCallback } from "react";
import {
  Check,
  Chips,
  CollapseBox,
  Layout,
  Message,
  Number,
  PathMappingTable,
  Section,
  Selector,
  Slider,
  Text,
  URLTestButton,
} from "../components";
import { seriesEnabledKey } from "../keys";
import { seriesTypeOptions } from "../options";

const SettingsSonarrView: FunctionComponent = () => {
  const baseUrlOverride = useCallback((settings: Settings) => {
    return settings.sonarr.base_url?.slice(1) ?? "";
  }, []);

  return (
    <Layout name="Sonarr">
      <CollapseBox>
        <CollapseBox.Control>
          <Section header="Use Sonarr">
            <Check label="Enabled" settingKey={seriesEnabledKey}></Check>
          </Section>
        </CollapseBox.Control>
        <CollapseBox.Content indent={false}>
          <Section header="Host">
            <Text label="Address" settingKey="settings-sonarr-ip"></Text>
            <Message>Hostname or IPv4 Address</Message>
            <Number label="Port" settingKey="settings-sonarr-port"></Number>
            <Text
              label="Base URL"
              icon="/"
              settingKey="settings-sonarr-base_url"
              override={baseUrlOverride}
              beforeStaged={(v) => "/" + v}
            ></Text>
            <Text label="API Key" settingKey="settings-sonarr-apikey"></Text>
            <Check label="SSL" settingKey="settings-sonarr-ssl"></Check>
            <URLTestButton category="sonarr"></URLTestButton>
          </Section>
          <Section header="Options">
            <Slider
              label="Minimum Score"
              settingKey="settings-general-minimum_score"
            ></Slider>
            <Chips
              label="Excluded Tags"
              settingKey="settings-sonarr-excluded_tags"
            ></Chips>
            <Message>
              Episodes from series with those tags (case sensitive) in Sonarr
              will be excluded from automatic download of subtitles.
            </Message>
            <Selector
              label="Excluded Series Types"
              settingKey="settings-sonarr-excluded_series_types"
              multiple
              options={seriesTypeOptions}
            ></Selector>
            <Message>
              Episodes from series with those types in Sonarr will be excluded
              from automatic download of subtitles.
            </Message>
            <Check
              label="Download Only Monitored"
              settingKey="settings-sonarr-only_monitored"
            ></Check>
            <Message>
              Automatic download of subtitles will only happen for monitored
              episodes in Sonarr.
            </Message>
            <Check
              label="Defer searching of subtitles until scheduled task execution"
              settingKey="settings-sonarr-defer_search_signalr"
            ></Check>
            <Message>
              If enabled, this option will prevent Bazarr from searching
              subtitles as soon as episodes are imported.
            </Message>
            <Message>
              Search can be triggered using this command: `curl -d
              "sonarr_episodefile_id=$sonarr_episodefile_id" -H "x-api-key:
              ###############################" -X POST
              http://localhost:6767/api/webhooks/sonarr`
            </Message>
            <Check
              label="Exclude season zero (extras)"
              settingKey="settings-sonarr-exclude_season_zero"
            ></Check>
            <Message>
              Episodes from season zero (extras) from automatic download of
              subtitles.
            </Message>
          </Section>
          <Section header="Path Mappings">
            <PathMappingTable type="sonarr"></PathMappingTable>
          </Section>
        </CollapseBox.Content>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsSonarrView;
