import { FunctionComponent } from "react";
import { Code } from "@mantine/core";
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
  Text,
  URLTestButton,
} from "@/pages/Settings/components";
import { moviesEnabledKey } from "@/pages/Settings/keys";
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
            leftSection="/"
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
          <Check
            label="Sync with Radarr on live connection establishment"
            settingKey="settings-radarr-movies_sync_on_live"
          ></Check>
          <Message>
            When Bazarr connects or reconnects to Radarr, run a movies
            synchronization to make sure that we're up-to-date.
          </Message>
          <Chips
            label="Excluded Tags"
            settingKey="settings-radarr-excluded_tags"
            sanitizeFn={(values: string[] | null) =>
              values?.map((item) =>
                item.replace(/[^a-z0-9_-]/gi, "").toLowerCase(),
              )
            }
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
            label="Sync Only Monitored Movies"
            settingKey={"settings-radarr-sync_only_monitored_movies"}
          ></Check>
          <CollapseBox
            settingKey={"settings-radarr-sync_only_monitored_movies"}
          >
            <Message>
              If enabled, only movies with a monitored status in Radarr will be
              synced. If you make changes to a specific unmonitored Radarr movie
              and you want Bazarr to know about those changes, simply toggle the
              monitored status back on in Radarr and Bazarr will sync any
              changes.
            </Message>
          </CollapseBox>

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
              {`curl -H "Content-Type: application/json" -H "X-API-KEY: ###############################" -X POST 
                -d '{ "eventType": "Download", "movieFile": { "id": "$radarr_moviefile_id" } }' 
                http://localhost:6767/api/webhooks/radarr
              `}
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
