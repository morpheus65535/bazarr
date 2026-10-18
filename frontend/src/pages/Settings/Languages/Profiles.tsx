import {
  FunctionComponent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { Text as MantineText } from "@mantine/core";
import { useLanguages } from "@/apis/hooks";
import ProfileEditor from "@/components/forms/ProfileEditor";
import {
  Check,
  Chips,
  CollapseBox,
  Layout,
  Message,
  Section,
} from "@/pages/Settings/components";
import { enabledLanguageKey, languageProfileKey } from "@/pages/Settings/keys";
import { useStagedValues } from "@/pages/Settings/utilities/FormValues";
import { LanguageSelector, ProfileSelector } from "./components";
import {
  createEnhancedProfile,
  prepareProfileForEditing,
} from "./profileModel";
import ProfilesList from "./ProfilesList";
import { useLatestEnabledLanguages } from "./useLatestLanguages";
import { useProfileActions } from "./useProfileActions";

interface EditorSession {
  profile: Language.Profile;
  isCreating: boolean;
}

const SettingsLanguageProfilesView: FunctionComponent = () => {
  const [session, setSession] = useState<EditorSession | null>(null);
  const [isDraftDirty, setDraftDirty] = useState(false);

  const openEditor = useCallback(
    (profile: Language.Profile, isCreating: boolean) => {
      setSession({ profile, isCreating });
      setDraftDirty(false);
    },
    [],
  );

  const closeEditor = useCallback(() => {
    setSession(null);
    setDraftDirty(false);
  }, []);

  return (
    <Layout
      name="Languages"
      isEditorActive={session !== null}
      isDraftDirty={isDraftDirty}
    >
      <ProfilesSections
        session={session}
        onOpen={openEditor}
        onClose={closeEditor}
        onDraftDirtyChange={setDraftDirty}
      ></ProfilesSections>
    </Layout>
  );
};

interface ProfilesSectionsProps {
  session: EditorSession | null;
  onOpen: (profile: Language.Profile, isCreating: boolean) => void;
  onClose: () => void;
  onDraftDirtyChange: (isDirty: boolean) => void;
}

const ProfilesSections: FunctionComponent<ProfilesSectionsProps> = ({
  onClose,
  onDraftDirtyChange,
  onOpen,
  session,
}) => {
  const { data: languages } = useLanguages();
  const enabledLanguages = useLatestEnabledLanguages() ?? [];
  const stagedValues = useStagedValues();
  const { profiles, updateProfile, removeProfile, createProfileId } =
    useProfileActions();

  const returnFocusRef = useRef<string | null>(null);
  const firstEnabledLanguage = enabledLanguages[0]?.code2;
  const isSaveRequired = languageProfileKey in stagedValues;

  const openCreate = useCallback(() => {
    returnFocusRef.current = "profile-create-action";
    onOpen(createEnhancedProfile(createProfileId, firstEnabledLanguage), true);
  }, [createProfileId, firstEnabledLanguage, onOpen]);

  const openEdit = useCallback(
    (profile: Language.Profile) => {
      returnFocusRef.current = `profile-edit-${profile.profileId}`;
      onOpen(prepareProfileForEditing(profile), false);
    },
    [onOpen],
  );

  const handleApply = useCallback(
    (profile: Language.Profile) => {
      updateProfile(profile);
      onClose();
    },
    [onClose, updateProfile],
  );

  // Return focus to the control that opened the editor once the list is back.
  useEffect(() => {
    if (session !== null || returnFocusRef.current === null) {
      return;
    }

    document.getElementById(returnFocusRef.current)?.focus();
    returnFocusRef.current = null;
  }, [session]);

  if (session) {
    return (
      <ProfileEditor
        key={session.profile.profileId}
        profile={session.profile}
        languages={enabledLanguages}
        isCreating={session.isCreating}
        onApply={handleApply}
        onCancel={onClose}
        onDirtyChange={onDraftDirtyChange}
      ></ProfileEditor>
    );
  }

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
          <ProfilesList
            profiles={profiles}
            languages={enabledLanguages}
            canCreate
            isSaveRequired={isSaveRequired}
            onCreate={openCreate}
            onEdit={openEdit}
            onRemove={removeProfile}
          ></ProfilesList>
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
