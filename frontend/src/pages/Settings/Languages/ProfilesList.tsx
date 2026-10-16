import { FunctionComponent, useCallback, useMemo } from "react";
import { Alert, Badge, Button, Card, Group, Stack, Text } from "@mantine/core";
import { modals } from "@mantine/modals";
import { faLayerGroup, faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { summarizeProfile } from "@/utilities/languageProfileSummary";
import { createLanguageNameResolver } from "@/utilities/languages";
import styles from "./ProfilesList.module.scss";

export interface ProfilesListProps {
  profiles: readonly Language.Profile[];
  languages: readonly Language.Info[];
  canCreate: boolean;
  isSaveRequired: boolean;
  onCreate: () => void;
  onEdit: (profile: Language.Profile) => void;
  onRemove: (index: number) => void;
}

const ProfilesList: FunctionComponent<ProfilesListProps> = ({
  canCreate,
  isSaveRequired,
  languages,
  onCreate,
  onEdit,
  onRemove,
  profiles,
}) => {
  const resolveLanguageName = useMemo(
    () => createLanguageNameResolver(languages),
    [languages],
  );

  const summaries = useMemo(
    () =>
      profiles.map((profile) => summarizeProfile(profile, resolveLanguageName)),
    [profiles, resolveLanguageName],
  );

  const requestDelete = useCallback(
    (profile: Language.Profile, index: number) => {
      modals.openConfirmModal({
        title: "Delete profile?",
        children: (
          <Text size="sm">
            Delete “{profile.name || "this profile"}”? It is removed only when
            you click Save.
          </Text>
        ),
        labels: { confirm: "Delete", cancel: "Cancel" },
        confirmProps: { color: "red" },
        onConfirm: () => onRemove(index),
      });
    },
    [onRemove],
  );

  if (profiles.length === 0) {
    return (
      <Card withBorder padding="lg" className={styles.emptyState}>
        <Stack align="center" gap="xs">
          <FontAwesomeIcon icon={faLayerGroup} size="2x" />
          <Text fw={600}>No language profiles yet</Text>
          <Text size="sm" c="dimmed" ta="center">
            Create a profile to describe the subtitles you want for your media.
          </Text>
          <Button
            id="profile-create-action"
            disabled={!canCreate}
            onClick={onCreate}
            leftSection={<FontAwesomeIcon icon={faPlus} />}
          >
            Create profile
          </Button>
        </Stack>
      </Card>
    );
  }

  return (
    <Stack gap="md">
      {isSaveRequired && (
        <Alert color="info" variant="light" role="status">
          You have unsaved profile changes. Click Save to apply them.
        </Alert>
      )}

      <Group justify="space-between" align="center" wrap="wrap">
        <Text size="sm" c="dimmed">
          {profiles.length} profile{profiles.length === 1 ? "" : "s"} configured
        </Text>
        <Button
          id="profile-create-action"
          disabled={!canCreate}
          onClick={onCreate}
          leftSection={<FontAwesomeIcon icon={faPlus} />}
        >
          Create profile
        </Button>
      </Group>

      <Stack gap="sm">
        {profiles.map((profile, index) => {
          const summary = summaries[index];

          return (
            <Card
              key={profile.profileId}
              withBorder
              padding="md"
              className={styles.entry}
            >
              <Stack gap="xs">
                <Group
                  justify="space-between"
                  align="flex-start"
                  wrap="wrap"
                  gap="xs"
                >
                  <Group gap="xs" align="center" wrap="wrap">
                    <Text fw={600}>{profile.name || "Untitled profile"}</Text>
                    {profile.profileType === "enhanced" && (
                      <Badge size="xs" variant="light" color="brand">
                        Enhanced
                      </Badge>
                    )}
                    {profile.tag && (
                      <Badge size="xs" variant="light" color="secondary">
                        {profile.tag}
                      </Badge>
                    )}
                    <Badge size="xs" variant="default">
                      {summary.requirements.length} requirement
                      {summary.requirements.length === 1 ? "" : "s"}
                    </Badge>
                  </Group>
                  <Group gap="xs">
                    <Button
                      id={`profile-edit-${profile.profileId}`}
                      size="xs"
                      variant="default"
                      onClick={() => onEdit(profile)}
                    >
                      Edit
                    </Button>
                    <Button
                      size="xs"
                      variant="subtle"
                      color="danger"
                      onClick={() => requestDelete(profile, index)}
                    >
                      Delete
                    </Button>
                  </Group>
                </Group>

                <Stack gap={4}>
                  {summary.requirements.map((requirement, requirementIndex) => (
                    <Text key={requirementIndex} size="sm">
                      {requirement.text}
                    </Text>
                  ))}
                  <Text size="sm" c="dimmed">
                    {summary.completion}
                  </Text>
                </Stack>

                {summary.restrictions.length > 0 && (
                  <div className={styles.restrictions}>
                    {summary.restrictions.map((restriction) => (
                      <Badge
                        key={restriction}
                        size="xs"
                        variant="light"
                        color="secondary"
                      >
                        {restriction}
                      </Badge>
                    ))}
                  </div>
                )}
              </Stack>
            </Card>
          );
        })}
      </Stack>
    </Stack>
  );
};

export default ProfilesList;
