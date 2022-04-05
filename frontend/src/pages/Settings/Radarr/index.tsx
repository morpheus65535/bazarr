import { FunctionComponent, useCallback } from "react";
import {
  Check,
  Chips,
  CollapseBox,
  Group,
  Input,
  Layout,
  Message,
  PathMappingTable,
  Slider,
  Text,
  URLTestButton,
} from "../components";
import { moviesEnabledKey } from "../keys";

const SettingsRadarrView: FunctionComponent = () => {
  const baseUrlOverride = useCallback((settings: Settings) => {
    return settings.radarr.base_url?.slice(1) ?? "";
  }, []);

  return (
    <Layout name="Radarr">
      <CollapseBox>
        <CollapseBox.Control>
          <Group header="Use Radarr">
            <Input>
              <Check label="Enabled" settingKey={moviesEnabledKey}></Check>
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
              <Text
                settingKey="settings-radarr-port"
                numberWithArrows={true}
              ></Text>
            </Input>
            <Input name="Base URL">
              {/* <InputGroup>
                <InputGroup.Prepend>
                  <InputGroup.Text>/</InputGroup.Text>
                </InputGroup.Prepend> */}
              <Text
                settingKey="settings-radarr-base_url"
                override={baseUrlOverride}
                beforeStaged={(v) => "/" + v}
              ></Text>
              {/* </InputGroup> */}
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
            <Input>
              <Check
                label="Defer searching of subtitles until scheduled task execution"
                settingKey="settings-radarr-defer_search_signalr"
              ></Check>
              <Message>
                If enabled, this option will prevent Bazarr from searching
                subtitles as soon as movies are imported.
              </Message>
              <Message>
                Search can be triggered using this command: `curl -d
                "radarr_moviefile_id=$radarr_moviefile_id" -H "x-api-key:
                ###############################" -X POST
                http://localhost:6767/api/webhooks/radarr`
              </Message>
            </Input>
          </Group>
          <Group header="Path Mappings">
            <PathMappingTable type="radarr"></PathMappingTable>
          </Group>
        </CollapseBox.Content>
      </CollapseBox>
    </Layout>
  );
};

export default SettingsRadarrView;
