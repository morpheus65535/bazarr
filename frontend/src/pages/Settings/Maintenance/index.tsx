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
    </Layout>
  );
};

export default SettingsMaintenanceView;
