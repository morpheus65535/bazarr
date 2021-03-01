import React, { FunctionComponent } from "react";
import { uiPageSizeKey } from "../../@storage/local";
import { Group, Input, Selector, SettingsProvider } from "../components";
import { pageSizeOptions } from "./options";

const SettingsUIView: FunctionComponent = () => {
  return (
    <SettingsProvider title="Interface - Bazarr (Settings)">
      <Group header="UI">
        <Input name="Page Size">
          <Selector
            options={pageSizeOptions}
            settingKey={uiPageSizeKey}
            override={(_, s) => s.site.pageSize}
          ></Selector>
        </Input>
      </Group>
    </SettingsProvider>
  );
};

export default SettingsUIView;
