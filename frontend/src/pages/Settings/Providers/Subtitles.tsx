import { FunctionComponent } from "react";
import { Layout, Section } from "@/pages/Settings/components";
import { ProviderView } from "./components";
import { ProviderList } from "./list";

const SettingsProvidersSubtitlesView: FunctionComponent = () => {
  return (
    <Layout name="Providers">
      <Section header="Enabled Providers">
        <ProviderView
          availableOptions={ProviderList}
          settingsKey="settings-general-enabled_providers"
        ></ProviderView>
      </Section>
    </Layout>
  );
};

export default SettingsProvidersSubtitlesView;
