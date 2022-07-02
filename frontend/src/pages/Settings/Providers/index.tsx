import { FunctionComponent } from "react";
import { Layout, Section } from "../components";
import { ProviderView } from "./components";

const SettingsProvidersView: FunctionComponent = () => {
  return (
    <Layout name="Providers">
      <Section header="Providers">
        <ProviderView></ProviderView>
      </Section>
    </Layout>
  );
};

export default SettingsProvidersView;
