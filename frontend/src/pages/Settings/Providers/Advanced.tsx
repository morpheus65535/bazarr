import { FunctionComponent } from "react";
import { Check, Layout, Message, Section } from "@/pages/Settings/components";

const SettingsProvidersAdvancedView: FunctionComponent = () => {
  return (
    <Layout name="Providers">
      <Section header="Advanced">
        <Check
          label="Disable All Providers HTTPS Certificate Validation"
          settingKey="settings-general-disable_all_providers_ssl_verify"
        ></Check>
        <Message>
          Disable all providers HTTPS certificate validation. Do not change
          unless you get SSL issues with providers and you understand the risks.
        </Message>
      </Section>
    </Layout>
  );
};

export default SettingsProvidersAdvancedView;
