import { FunctionComponent } from "react";
import { Group, Input, Layout } from "../components";
import { ProviderModal, ProviderView } from "./components";

const SettingsProvidersView: FunctionComponent = () => {
  return (
    <Layout name="Providers">
      <Group header="Providers">
        <Input>
          <ProviderView></ProviderView>
        </Input>
      </Group>
      <ProviderModal></ProviderModal>
    </Layout>
  );
};

export default SettingsProvidersView;
