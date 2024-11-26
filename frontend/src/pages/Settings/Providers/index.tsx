import { FunctionComponent } from "react";
import { Anchor } from "@mantine/core";
import {
  CollapseBox,
  Layout,
  Message,
  Password,
  Section,
  Selector,
  Text,
} from "@/pages/Settings/components";
import { antiCaptchaOption } from "@/pages/Settings/Providers/options";
import { ProviderView } from "./components";
import { IntegrationList, ProviderList } from "./list";

const SettingsProvidersView: FunctionComponent = () => {
  return (
    <Layout name="Providers">
      <Section header="Enabled Providers">
        <ProviderView
          availableOptions={ProviderList}
          settingsKey="settings-general-enabled_providers"
        ></ProviderView>
      </Section>
      <Section header="Anti-Captcha Options">
        <Selector
          clearable
          label={"Choose the anti-captcha provider you want to use"}
          placeholder="Select a provider"
          settingKey="settings-general-anti_captcha_provider"
          options={antiCaptchaOption}
        ></Selector>
        <Message></Message>
        <CollapseBox
          settingKey="settings-general-anti_captcha_provider"
          on={(value) => value === "anti-captcha"}
        >
          <Text
            label="Account Key"
            settingKey="settings-anticaptcha-anti_captcha_key"
          ></Text>
          <Anchor href="http://getcaptchasolution.com/eixxo1rsnw">
            Anti-Captcha.com
          </Anchor>
          <Message>Link to subscribe</Message>
        </CollapseBox>
        <CollapseBox
          settingKey="settings-general-anti_captcha_provider"
          on={(value) => value === "death-by-captcha"}
        >
          <Text
            label="Username"
            settingKey="settings-deathbycaptcha-username"
          ></Text>
          <Password
            label="Password"
            settingKey="settings-deathbycaptcha-password"
          ></Password>
          <Anchor href="https://www.deathbycaptcha.com">
            DeathByCaptcha.com
          </Anchor>
          <Message>Link to subscribe</Message>
        </CollapseBox>
      </Section>
      <Section header="Integrations">
        <ProviderView
          availableOptions={IntegrationList}
          settingsKey="settings-general-enabled_integrations"
        ></ProviderView>
      </Section>
    </Layout>
  );
};

export default SettingsProvidersView;
