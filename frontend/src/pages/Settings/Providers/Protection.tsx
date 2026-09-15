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
import { antiCaptchaOption } from "./options";

const SettingsProvidersProtectionView: FunctionComponent = () => {
  return (
    <Layout name="Providers">
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
        <CollapseBox
          settingKey="settings-general-anti_captcha_provider"
          on={(value) => value === "captchaai"}
        >
          <Text
            label="Account Key"
            settingKey="settings-captchaai-captchaai_key"
          ></Text>
          <Anchor href="https://captchaai.com">CaptchaAI.com</Anchor>
          <Message>Link to subscribe</Message>
        </CollapseBox>
      </Section>
    </Layout>
  );
};

export default SettingsProvidersProtectionView;
