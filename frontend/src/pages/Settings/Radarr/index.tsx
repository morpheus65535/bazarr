import { Code } from "@mantine/core";
import { FunctionComponent } from "react";
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
import { moviesEnabledKey } from "../keys";
import { timeoutOptions } from "./options";

const SettingsRadarrView: FunctionComponent = () => {
  return (
    <Layout name="Radarr">
      <Section header="Use Radarr">
        <Check label="Enabled" settingKey={moviesEnabledKey}></Check>
      </Section>
      <CollapseBox settingKey={moviesEnabledKey}>
        <Section header="Host">
          <Text label="Address" settingKey="settings-radarr-ip"></Text>
          <Message>Hostname or IPv4 Address</Message>
          <Number label="Port" settingKey="settings-radarr-port"></Number>
          <Text
            label="Base URL"
            icon="/"
            settingKey="settings-radarr-base_url"
            settingOptions={{
              onLoaded: (s) => s.radarr.base_url?.slice(1) ?? "",
              onSubmit: (v) => "/" + v,
            }}
          ></Text>
          <Selector
            label="HTTP Timeout"
            options={timeoutOptions}
            settingKey="settings-radarr-http_timeout"
          ></Selector>
          <Text label="API Key" settingKey="settings-radarr-apikey"></Text>
          <Check label="SSL" settingKey="settings-radarr-ssl"></Check>
          <URLTestButton category="radarr"></URLTestButton>
        </Section>
        <Section header="Options">
          <Slider
            label="Minimum Score"
            settingKey="settings-general-minimum_score_movie"
          ></Slider>
          <Chips
            label="Excluded Tags"
            settingKey="settings-radarr-excluded_tags"
          ></Chips>
          <Message>
            Movies with those tags (case sensitive) in Radarr will be excluded
            from automatic download of subtitles.
          </Message>
          <Check
            label="Download Only Monitored"
            settingKey="settings-radarr-only_monitored"
          ></Check>
          <Message>
            Automatic download of subtitles will only happen for monitored
            movies in Radarr.
          </Message>

          <Check
            label="Defer searching of subtitles until scheduled task execution"
            settingKey="settings-radarr-defer_search_signalr"
          ></Check>
          <Message>
            If enabled, this option will prevent Bazarr from searching subtitles
            as soon as movies are imported.
          </Message>
          <Message>
            Search can be triggered using this command
            <Code>
              curl -d "radarr_moviefile_id=$radarr_moviefile_id" -H "x-api-key:
              ###############################" -X POST
              http://localhost:6767/api/webhooks/radarr
            </Code>
          </Message>
        </Section>
        <Section header="Path Mappings">
          <PathMappingTable type="radarr"></PathMappingTable>
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsRadarrView;
