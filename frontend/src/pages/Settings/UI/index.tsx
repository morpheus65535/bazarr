import { FunctionComponent } from "react";
import { Layout, Section, Selector } from "@/pages/Settings/components";
import { uiPageSizeKey } from "@/utilities/storage";
import { colorSchemeOptions, pageSizeOptions } from "./options";

const SettingsUIView: FunctionComponent = () => {
  return (
    <Layout name="Interface">
      <Section header="List View">
        <Selector
          label="Page Size"
          options={pageSizeOptions}
          settingKey={uiPageSizeKey}
          defaultValue={50}
        ></Selector>
      </Section>
      <Section header="Style">
        <Selector
          label="Theme"
          options={colorSchemeOptions}
          settingKey="settings-general-theme"
          defaultValue={"auto"}
        ></Selector>
      </Section>
    </Layout>
  );
};

export default SettingsUIView;
