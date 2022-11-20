import { uiPageSizeKey } from "@/utilities/storage";
import { FunctionComponent } from "react";
import { Layout, Section, Selector } from "../components";
import { pageSizeOptions } from "./options";

const SettingsUIView: FunctionComponent = () => {
  return (
    <Layout name="Interface">
      <Section header="UI">
        <Selector
          label="Page Size"
          options={pageSizeOptions}
          settingKey={uiPageSizeKey}
          defaultValue={50}
        ></Selector>
      </Section>
    </Layout>
  );
};

export default SettingsUIView;
