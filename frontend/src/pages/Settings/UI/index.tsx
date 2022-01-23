import { uiPageSizeKey, usePageSize } from "@/utilities/storage";
import React, { FunctionComponent } from "react";
import { Group, Input, Layout, Selector } from "../components";
import { pageSizeOptions } from "./options";

const SettingsUIView: FunctionComponent = () => {
  const [pageSize] = usePageSize();
  return (
    <Layout name="Interface">
      <Group header="UI">
        <Input name="Page Size">
          <Selector
            options={pageSizeOptions}
            settingKey={uiPageSizeKey}
            override={(_) => pageSize}
          ></Selector>
        </Input>
      </Group>
    </Layout>
  );
};

export default SettingsUIView;
