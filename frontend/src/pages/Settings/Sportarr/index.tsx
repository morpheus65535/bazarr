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
} from "@/pages/Settings/components";
import { sportsEnabledKey } from "@/pages/Settings/keys";
import { timeoutOptions } from "./options";

const SettingsSportarrView: FunctionComponent = () => {
  return (
    <Layout name="Sportarr">
      <Section header="Use Sportarr">
        <Check label="Enabled" settingKey={sportsEnabledKey}></Check>
      </Section>
      <CollapseBox settingKey={sportsEnabledKey}>
        <Section header="Host">
          <Text label="Address" settingKey="settings-sportarr-ip"></Text>
          <Message>Hostname or IPv4 Address</Message>
          <Number label="Port" settingKey="settings-sportarr-port"></Number>
          <Text
            label="Base URL"
            leftSection="/"
            settingKey="settings-sportarr-base_url"
            settingOptions={{
              onLoaded: (s) => s.sportarr.base_url?.slice(1) ?? "",
              onSubmit: (v) => "/" + v,
            }}
          ></Text>
          <Selector
            label="HTTP Timeout"
            options={timeoutOptions}
            settingKey="settings-sportarr-http_timeout"
          ></Selector>
          <Text label="API Key" settingKey="settings-sportarr-apikey"></Text>
          <Check label="SSL" settingKey="settings-sportarr-ssl"></Check>
          <URLTestButton category="sportarr"></URLTestButton>
        </Section>
        <Section header="Options">
          <Slider
            label="Minimum Score For Sports Events"
            settingKey="settings-general-minimum_score"
          ></Slider>
          <Message>
            A sports event carries a season and an episode number from Sportarr
            and is scored the same way an episode is, so it shares this setting.
          </Message>
          <Chips
            label="Excluded Tags"
            settingKey="settings-sportarr-excluded_tags"
            sanitizeFn={(values: string[] | null) =>
              values?.map((item) =>
                item.replace(/[^a-z0-9_-]/gi, "").toLowerCase(),
              )
            }
          ></Chips>
          <Message>
            Events from leagues with those tags (case sensitive) in Sportarr
            will be excluded from automatic download of subtitles.
          </Message>
          <Chips
            label="Excluded Sports"
            settingKey="settings-sportarr-excluded_sports"
          ></Chips>
          <Message>
            Events from leagues of those sports will be excluded from automatic
            download of subtitles. Sport is the closest a league has to a series
            type.
          </Message>
          <Check
            label="Download Only Monitored"
            settingKey="settings-sportarr-only_monitored"
          ></Check>
          <Message>
            Automatic download of subtitles will only happen for monitored
            events in Sportarr.
          </Message>
          <Check
            label="Sync Only Monitored Leagues"
            settingKey="settings-sportarr-sync_only_monitored_leagues"
          ></Check>
          <Check
            label="Sync Only Monitored Events"
            settingKey="settings-sportarr-sync_only_monitored_events"
          ></Check>
          <Message>
            Both are needed to skip unmonitored events during a sync. Skipped
            events stay in the database rather than being removed from it.
          </Message>
          <Check
            label="Use ffprobe Cache"
            settingKey="settings-sportarr-use_ffprobe_cache"
          ></Check>
          <Message>
            Reuse the stored media analysis when indexing subtitles instead of
            reading each file again.
          </Message>
        </Section>
        <Section header="Path Mappings">
          <PathMappingTable type="sportarr"></PathMappingTable>
        </Section>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsSportarrView;
