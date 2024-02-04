import { antiCaptchaOption } from "@/pages/Settings/Providers/options";
import { Anchor } from "@mantine/core";
import { FunctionComponent } from "react";
import {
  CollapseBox,
  Layout,
  Message,
  Password,
  Section,
  Selector,
  Text,
} from "../components";
import { ProviderView } from "./components";

const SettingsProvidersView: FunctionComponent = () => {
  return (
    <Layout name="Providers">
      <Section header="Providers">
        <ProviderView></ProviderView>
      </Section>
      <Section header="Anti-Captcha Options">
        <Selector
          clearable
          label={"Choose the anti-captcha provider you want to use"}
          placeholder="Select a provider"
          settingKey="settings-general-anti_captcha_provider"
          settingOptions={{ onSubmit: (v) => (v === undefined ? "None" : v) }}
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
    </Layout>
  );
};

export default SettingsProvidersView;
