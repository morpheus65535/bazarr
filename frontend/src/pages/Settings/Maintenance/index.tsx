import { FunctionComponent } from "react";
import {
  Check,
  Layout,
  Message,
  Section,
  Selector,
  Text,
} from "@/pages/Settings/components";
import { Environment } from "@/utilities";
import { branchOptions } from "./options";

const SettingsMaintenanceView: FunctionComponent = () => {
  return (
    <Layout name="Maintenance">
      <Section header="Updates" hidden={!Environment.canUpdate}>
        <Check
          label="Automatic"
          settingKey="settings-general-auto_update"
        ></Check>
        <Message>Automatically download and install updates</Message>
        <Selector
          options={branchOptions}
          settingKey="settings-general-branch"
        ></Selector>
        <Message>Branch used by update mechanism</Message>
      </Section>
      <Section header="Logging">
        <Check label="Debug" settingKey="settings-general-debug"></Check>
        <Message>Debug logging should only be enabled temporarily</Message>
        <Text
          label="Include Filter"
          settingKey="settings-log-include_filter"
        ></Text>
        <Text
          label="Exclude Filter"
          settingKey="settings-log-exclude_filter"
        ></Text>
        <Check
          label="Use Regular Expressions (Regex)"
          settingKey="settings-log-use_regex"
        ></Check>
        <Check
          label="Ignore Case"
          settingKey="settings-log-ignore_case"
        ></Check>
      </Section>
      <Section header="Analytics">
        <Check label="Enable" settingKey="settings-analytics-enabled"></Check>
        <Message>
          Send anonymous usage information, nothing that can identify you. This
          includes information on which providers you use, what languages you
          search for, Bazarr, Python, Sonarr, Radarr and what OS version you are
          using. We will use this information to prioritize features and bug
          fixes. Please, keep this enabled as this is the only way we have to
          better understand how you use Bazarr.
        </Message>
      </Section>
    </Layout>
  );
};

export default SettingsMaintenanceView;
