import React, { FunctionComponent } from "react";
import {
  Check,
  Chips,
  CollapseBox,
  Group,
  Input,
  Message,
  Selector,
  SettingsProvider,
  Slider,
} from "../components";
import { seriesEnabledKey } from "../keys";
import { seriesTypeOptions } from "../options";

interface Props {}

const SettingsSeriesView: FunctionComponent<Props> = () => {
  return (
    <SettingsProvider title="Series - Bazarr (Settings)">
      <CollapseBox>
        <CollapseBox.Control>
          <Group header="Use Series">
            <Input>
              <Check label="Enabled" settingKey={seriesEnabledKey}></Check>
            </Input>
          </Group>
        </CollapseBox.Control>
        <CollapseBox.Content indent={false}>
          <Group header="Options">
            <Input name="Minimum Score">
              <Slider settingKey="settings-general-minimum_score"></Slider>
            </Input>
            <Input name="Excluded Tags">
              <Chips settingKey="settings-series-excluded_tags"></Chips>
              <Message>
                Episodes from series with those tags (case sensitive) will be
                excluded from automatic download of subtitles.
              </Message>
            </Input>
            <Input name="Excluded Series Types">
              <Selector
                settingKey="settings-series-excluded_series_types"
                multiple
                options={seriesTypeOptions}
              ></Selector>
              <Message>
                Episodes from series with those types will be excluded from
                automatic download of subtitles.
              </Message>
            </Input>
            <Input>
              <Check
                label="Download Only Monitored"
                settingKey="settings-series-only_monitored"
              ></Check>
              <Message>
                Automatic download of subtitles will only happen for monitored
                episodes.
              </Message>
            </Input>
          </Group>
        </CollapseBox.Content>
      </CollapseBox>
    </SettingsProvider>
  );
};

export default SettingsSeriesView;
