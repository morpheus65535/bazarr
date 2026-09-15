import { FunctionComponent } from "react";
import { Text as MantineText } from "@mantine/core";
import { useLanguages } from "@/apis/hooks";
import {
  Check,
  Chips,
  CollapseBox,
  Layout,
  Message,
  Section,
} from "@/pages/Settings/components";
import { enabledLanguageKey } from "@/pages/Settings/keys";
import { LanguageSelector, ProfileSelector } from "./components";
import Table from "./table";
import { useLatestEnabledLanguages } from "./useLatestLanguages";

const SettingsLanguageProfilesView: FunctionComponent = () => {
  return (
    <Layout name="Languages">
      <ProfilesSections></ProfilesSections>
    </Layout>
  );
};

const ProfilesSections: FunctionComponent = () => {
  const { data: languages } = useLanguages();
  const enabledLanguages = useLatestEnabledLanguages() ?? [];

  return (
    <>
      <Section header="Languages Profile">
        {enabledLanguages.length === 0 ? (
          <>
            <Message>
              Profiles are built from your enabled languages. Pick the languages
              you want subtitles for to get started:
            </Message>
            <LanguageSelector
              label="Languages Filter"
              placeholder="Select languages"
              settingKey={enabledLanguageKey}
              options={languages ?? []}
            ></LanguageSelector>
          </>
        ) : (
          <Table></Table>
        )}
      </Section>
      <Section
        header="Tag-Based Automatic Language Profile Selection"
        summary="Assign profiles via Sonarr/Radarr tags"
      >
        <Message>
          If enabled, Bazarr will look at the names of all tags of a Series from
          Sonarr (or a Movie from Radarr) to find a matching Bazarr language
          profile tag. It will use as the language profile the FIRST tag from
          Sonarr/Radarr that matches the tag of a Bazarr language profile
          EXACTLY. If multiple tags match, there is no guarantee as to which one
          will be used, so choose your tag names carefully. Also, if you update
          the tag names in Sonarr/Radarr, Bazarr will detect this and repeat the
          matching process for the affected shows. However, if a show's only
          matching tag is removed from Sonarr/Radarr, Bazarr will NOT remove the
          show's existing language profile for that reason. But if you wish to
          have language profiles removed automatically by tag value, simply
          enter a list of one or more tags in the{" "}
          <MantineText fw={700} span>
            Remove Profile Tags
          </MantineText>{" "}
          entry list below. If your video tag matches one of the tags in that
          list, then Bazarr will remove the language profile for that video. If
          there is a conflict between profile selection and profile removal,
          then profile removal wins out and is performed.
        </Message>
        <Check
          label="Series"
          settingKey="settings-general-serie_tag_enabled"
        ></Check>
        <Check
          label="Movies"
          settingKey="settings-general-movie_tag_enabled"
        ></Check>
        <Chips
          label="Remove Profile Tags"
          settingKey="settings-general-remove_profile_tags"
          sanitizeFn={(values: string[] | null) =>
            values?.map((item) =>
              item.replace(/[^a-z0-9_-]/gi, "").toLowerCase(),
            )
          }
        ></Chips>
        <Message>
          Enter tag values that will trigger a language profile removal. Leave
          empty if you don't want Bazarr to remove language profiles.
        </Message>
      </Section>
      <Section
        header="Default Language Profiles For Newly Added Shows"
        summary="Apply a profile automatically to new content"
      >
        <Check
          label="Series"
          settingKey="settings-general-serie_default_enabled"
        ></Check>
        <Message>
          Will apply only to Series added to Bazarr after enabling this option.
        </Message>

        <CollapseBox settingKey="settings-general-serie_default_enabled">
          <ProfileSelector
            label="Profile"
            placeholder="Select a profile"
            settingKey="settings-general-serie_default_profile"
          ></ProfileSelector>
        </CollapseBox>

        <Check
          label="Movies"
          settingKey="settings-general-movie_default_enabled"
        ></Check>
        <Message>
          Will apply only to Movies added to Bazarr after enabling this option.
        </Message>

        <CollapseBox settingKey="settings-general-movie_default_enabled">
          <ProfileSelector
            label="Profile"
            placeholder="Select a profile"
            settingKey="settings-general-movie_default_profile"
          ></ProfileSelector>
        </CollapseBox>
      </Section>
    </>
  );
};

export default SettingsLanguageProfilesView;
