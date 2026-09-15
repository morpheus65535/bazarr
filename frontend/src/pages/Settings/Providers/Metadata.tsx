import { FunctionComponent } from "react";
import { Layout, Section } from "@/pages/Settings/components";
import { ProviderView } from "./components";
import { IntegrationList } from "./list";

const SettingsProvidersMetadataView: FunctionComponent = () => {
  return (
    <Layout name="Providers">
      <Section header="Metadata Providers">
        <ProviderView
          availableOptions={IntegrationList}
          settingsKey="settings-general-enabled_integrations"
        ></ProviderView>
      </Section>
    </Layout>
  );
};

export default SettingsProvidersMetadataView;
