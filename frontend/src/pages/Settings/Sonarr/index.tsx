import { FunctionComponent } from "react";
import { Code } from "@mantine/core";
import {
  Check,
  Chips,
  CollapseBox,
  Layout,
  Message,
  MultiSelector,
  Number,
  PathMappingTable,
  Section,
  Selector,
  Slider,
  Text,
  URLTestButton,
} from "@/pages/Settings/components";
import { seriesEnabledKey } from "@/pages/Settings/keys";
import { seriesTypeOptions } from "@/pages/Settings/options";
import { timeoutOptions } from "./options";

const SettingsSonarrView: FunctionComponent = () => {
  return (
    <Layout name="Sonarr">
      <Section header="Use Sonarr">
        <Check label="Enabled" settingKey={seriesEnabledKey}></Check>
      </Section>
      <CollapseBox settingKey={seriesEnabledKey}>
        <Section header="Host">
          <Text label="Address" settingKey="settings-sonarr-ip"></Text>
          <Message>Hostname or IPv4 Address</Message>
          <Number label="Port" settingKey="settings-sonarr-port"></Number>
          <Text
            label="Base URL"
            leftSection="/"
            settingKey="settings-sonarr-base_url"
            settingOptions={{
              onLoaded: (s) => s.sonarr.base_url?.slice(1) ?? "",
              onSubmit: (v) => "/" + v,
            }}
          ></Text>
          <Selector
            label="HTTP Timeout"
            options={timeoutOptions}
            settingKey="settings-sonarr-http_timeout"
          ></Selector>
          <Text label="API Key" settingKey="settings-sonarr-apikey"></Text>
          <Check label="SSL" settingKey="settings-sonarr-ssl"></Check>
          <URLTestButton category="sonarr"></URLTestButton>
        </Section>
        <Section header="Options">
          <Slider
            label="Minimum Score For Episodes"
            settingKey="settings-general-minimum_score"
          ></Slider>
          <Chips
            label="Excluded Tags"
            settingKey="settings-sonarr-excluded_tags"
            sanitizeFn={(values: string[] | null) =>
              values?.map((item) =>
                item.replace(/[^a-z0-9_-]/gi, "").toLowerCase(),
              )
            }
          ></Chips>
          <Message>
            Episodes from series with those tags (case sensitive) in Sonarr will
            be excluded from automatic download of subtitles.
          </Message>
          <MultiSelector
            label="Excluded Series Types"
            placeholder="Select series types"
            settingKey="settings-sonarr-excluded_series_types"
            options={seriesTypeOptions}
          ></MultiSelector>
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
            If enabled, this option will prevent Bazarr from searching subtitles
            as soon as episodes are imported.
          </Message>
          <Message>
            Search can be triggered using this command:
            <Code>
              {`curl -H "Content-Type: application/json" -H "X-API-KEY: ###############################" -X POST 
                -d '{ "eventType": "Download", "episodeFiles": [ { "id": "$sonarr_episodefile_id" } ] }' 
                http://localhost:6767/api/webhooks/sonarr
              `}
            </Code>
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
      </CollapseBox>
    </Layout>
  );
};

export default SettingsSonarrView;
