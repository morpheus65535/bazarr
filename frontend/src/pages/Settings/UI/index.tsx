import React, { FunctionComponent } from "react";
import { uiPageSizeKey, usePageSize } from "utilities/storage";
import { Group, Input, Selector, SettingsProvider } from "../components";
import { pageSizeOptions } from "./options";

const SettingsUIView: FunctionComponent = () => {
  const [pageSize] = usePageSize();
  return (
    <SettingsProvider title="Interface - Bazarr (Settings)">
      <Group header="UI">
        <Input name="Page Size">
          <Selector
            options={pageSizeOptions}
            settingKey={uiPageSizeKey}
            override={(_) => pageSize}
          ></Selector>
        </Input>
      </Group>
    </SettingsProvider>
  );
};

export default SettingsUIView;
