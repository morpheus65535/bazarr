import { uiPageSizeKey, usePageSize } from "@/utilities/storage";
import { FunctionComponent } from "react";
import { Layout, Section, Selector } from "../components";
import { pageSizeOptions } from "./options";

const SettingsUIView: FunctionComponent = () => {
  const [pageSize] = usePageSize();
  return (
    <Layout name="Interface">
      <Section header="UI">
        <Selector
          label="Page Size"
          options={pageSizeOptions}
          location="storages"
          settingKey={uiPageSizeKey}
          settingOptions={{ onLoaded: () => pageSize }}
        ></Selector>
      </Section>
    </Layout>
  );
};

export default SettingsUIView;
