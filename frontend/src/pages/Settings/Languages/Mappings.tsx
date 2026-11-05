import { FunctionComponent } from "react";
import { Link } from "react-router";
import { Text as MantineText } from "@mantine/core";
import { Layout, Message, Section } from "@/pages/Settings/components";
import LanguageMappings from "./LanguageMappings";
import { useLatestEnabledLanguages } from "./useLatestLanguages";

const SettingsLanguageMappingsView: FunctionComponent = () => {
  return (
    <Layout name="Languages">
      <MappingsSection></MappingsSection>
    </Layout>
  );
};

const MappingsSection: FunctionComponent = () => {
  const enabledLanguages = useLatestEnabledLanguages() ?? [];

  return (
    <Section header="Language Mappings">
      <Message>
        Accept subtitles reported as one language as another canonical language.
        Mappings are one-way and apply globally.
      </Message>
      {enabledLanguages.length === 0 && (
        <Message type="warning">
          Mappings need at least one enabled language.{" "}
          <MantineText
            component={Link}
            to="/settings/languages/general"
            fw={500}
            c="info"
            td="none"
            span
          >
            Enable languages in the General tab
          </MantineText>
          .
        </Message>
      )}
      <LanguageMappings></LanguageMappings>
    </Section>
  );
};

export default SettingsLanguageMappingsView;
