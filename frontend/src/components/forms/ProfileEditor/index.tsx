import {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Alert,
  Button,
  Grid,
  Group,
  Stack,
  Text,
  TextInput,
  Title,
} from "@mantine/core";
import { modals } from "@mantine/modals";
import { faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { anyCutoff } from "@/components/forms/profileOptions";
import { summarizeProfile } from "@/utilities/languageProfileSummary";
import { createLanguageNameResolver } from "@/utilities/languages";
import AdvancedSettings from "./AdvancedSettings";
import { draftToProfile } from "./profileDraft";
import ProfileSummary from "./ProfileSummary";
import {
  ProfileValidationIssue,
  validateProfileDraft,
} from "./profileValidation";
import RequirementCard from "./RequirementCard";
import SearchCompletion from "./SearchCompletion";
import { useProfileDraft } from "./useProfileDraft";
import { useReorderAnimation } from "./useReorderAnimation";
import styles from "./ProfileEditor.module.scss";

export interface ProfileEditorProps {
  profile: Language.Profile;
  languages: readonly Language.Info[];
  isCreating: boolean;
  onApply: (profile: Language.Profile) => void;
  onCancel: () => void;
  onDirtyChange: (isDirty: boolean) => void;
}

const noIssues: ProfileValidationIssue[] = [];

// Keep in sync with the requirement exit animation in ProfileEditor.module.scss.
const removalDurationMs = 150;

const ProfileEditor: FunctionComponent<ProfileEditorProps> = ({
  isCreating,
  languages,
  onApply,
  onCancel,
  onDirtyChange,
  profile,
}) => {
  const controller = useProfileDraft(profile);
  const { draft, isDirty, removeGroup, removeItem } = controller;
  const [isValidationActive, setValidationActive] = useState(false);
  const [exitingGroupIds, setExitingGroupIds] = useState<number[]>([]);
  const [initialGroupIds] = useState(
    () => new Set(draft.groups.map((group) => group.id)),
  );
  const pendingFocusRef = useRef<string | null>(null);
  const removalTimersRef = useRef<number[]>([]);

  useEffect(
    () => () => {
      for (const timer of removalTimersRef.current) {
        window.clearTimeout(timer);
      }
    },
    [],
  );

  useEffect(() => {
    onDirtyChange(isDirty);
  }, [isDirty, onDirtyChange]);

  // Re-validate on every change, but only surface issues once the user has
  // tried to apply, so fixed errors clear as they edit.
  const validationIssues = useMemo(() => validateProfileDraft(draft), [draft]);
  const issues = isValidationActive ? validationIssues : noIssues;

  useEffect(() => {
    const targetId = pendingFocusRef.current;

    if (targetId === null) {
      return;
    }

    pendingFocusRef.current = null;
    document.getElementById(targetId)?.focus();
  }, [draft]);

  const resolveLanguageName = useMemo(
    () => createLanguageNameResolver(languages),
    [languages],
  );

  const languageData = useMemo(() => {
    const referenced = new Set(
      draft.groups.flatMap((group) => group.items.map((item) => item.language)),
    );

    const known = languages.map((language) => ({
      value: language.code2,
      label: language.name,
    }));

    const unavailable = [...referenced]
      .filter(
        (code) =>
          code.length > 0 &&
          !languages.some((language) => language.code2 === code),
      )
      .map((code) => ({ value: code, label: `${code} (unavailable)` }));

    return [...known, ...unavailable];
  }, [draft.groups, languages]);

  const summary = useMemo(
    () => summarizeProfile(draftToProfile(draft), resolveLanguageName),
    [draft, resolveLanguageName],
  );

  const isEnhanced = draft.profileType === "enhanced";

  const highlightedRequirementIndex = useMemo(() => {
    if (!isEnhanced || draft.cutoff === null || draft.cutoff === anyCutoff) {
      return null;
    }

    const index = draft.groups.findIndex((group) => group.id === draft.cutoff);

    return index === -1 ? null : index;
  }, [draft.cutoff, draft.groups, isEnhanced]);

  const orderKey = useMemo(
    () => draft.groups.map((group) => group.id).join(","),
    [draft.groups],
  );
  const { capture: capturePositions, containerRef: requirementsRef } =
    useReorderAnimation(orderKey);

  const handleMoveGroup = useCallback(
    (group: Language.EnhancedGroup, direction: -1 | 1) => {
      capturePositions();
      controller.moveGroup(group.id, direction);
    },
    [capturePositions, controller],
  );

  const issuesForGroup = useCallback(
    (groupId: number) =>
      issues.filter(
        (issue) => issue.field === "requirements" && issue.groupId === groupId,
      ),
    [issues],
  );

  const nameError = issues.find((issue) => issue.field === "name")?.message;
  const tagError = issues.find((issue) => issue.field === "tag")?.message;
  const requirementError = issues.find(
    (issue) => issue.field === "requirements" && issue.groupId === undefined,
  )?.message;

  const focusFirstIssue = useCallback(
    (issuesToFocus: ProfileValidationIssue[]) => {
      const [first] = issuesToFocus;

      if (first === undefined) {
        return;
      }

      const targetId =
        first.itemId !== undefined
          ? `profile-language-${first.itemId}`
          : first.groupId !== undefined
            ? `profile-requirement-${first.groupId}`
            : `profile-${first.field}`;

      document.getElementById(targetId)?.focus();
    },
    [],
  );

  const handleApply = useCallback(() => {
    setValidationActive(true);

    if (validationIssues.length > 0) {
      focusFirstIssue(validationIssues);
      return;
    }

    onApply(draftToProfile(draft));
  }, [draft, focusFirstIssue, onApply, validationIssues]);

  const requestCancel = useCallback(() => {
    if (!isDirty) {
      onCancel();
      return;
    }

    modals.openConfirmModal({
      title: "Discard changes?",
      children: (
        <Text size="sm">
          Your edits to this profile have not been applied yet.
        </Text>
      ),
      labels: { confirm: "Discard", cancel: "Keep editing" },
      confirmProps: { color: "red" },
      onConfirm: onCancel,
    });
  }, [isDirty, onCancel]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") {
        return;
      }

      if (document.querySelector('[role="dialog"]')) {
        return;
      }

      event.preventDefault();
      requestCancel();
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [requestCancel]);

  const handleRemoveItem = useCallback(
    (group: Language.EnhancedGroup, itemId: number) => {
      const index = group.items.findIndex((item) => item.id === itemId);
      const next = group.items[index + 1] ?? group.items[index - 1];

      removeItem(group.id, itemId);
      pendingFocusRef.current = next
        ? `profile-language-${next.id}`
        : `profile-add-language-${group.id}`;
    },
    [removeItem],
  );

  const removeRequirement = useCallback(
    (group: Language.EnhancedGroup) => {
      const index = draft.groups.findIndex((value) => value.id === group.id);
      const next = draft.groups[index + 1] ?? draft.groups[index - 1];

      // Fade the requirement out, then remove it so the FLIP animation slides
      // the remaining requirements into its place.
      capturePositions();
      setExitingGroupIds((ids) => [...ids, group.id]);

      const timer = window.setTimeout(() => {
        removeGroup(group.id);
        setExitingGroupIds((ids) => ids.filter((id) => id !== group.id));
        pendingFocusRef.current = next
          ? `profile-requirement-${next.id}`
          : "profile-requirements";
      }, removalDurationMs);

      removalTimersRef.current.push(timer);
    },
    [capturePositions, draft.groups, removeGroup],
  );

  const requestRemoveGroup = useCallback(
    (group: Language.EnhancedGroup) => {
      if (group.items.length === 0) {
        removeRequirement(group);
        return;
      }

      modals.openConfirmModal({
        title: "Remove requirement?",
        children: (
          <Text size="sm">
            This removes {group.items.length} language
            {group.items.length === 1 ? "" : "s"} from the profile. You can
            still cancel the edit afterwards.
          </Text>
        ),
        labels: { confirm: "Remove", cancel: "Keep" },
        confirmProps: { color: "red" },
        onConfirm: () => removeRequirement(group),
      });
    },
    [removeRequirement],
  );

  const toggleGroupCutoff = useCallback(
    (groupId: number) =>
      controller.setCutoff(draft.cutoff === groupId ? null : groupId),
    [controller, draft.cutoff],
  );

  const toggleItemCutoff = useCallback(
    (itemId: number) =>
      controller.setCutoff(draft.cutoff === itemId ? null : itemId),
    [controller, draft.cutoff],
  );

  return (
    <Stack gap="lg" className={styles.editor}>
      <Group
        justify="space-between"
        align="center"
        wrap="wrap"
        gap="sm"
        className={styles.header}
      >
        <Title order={3}>
          {isCreating ? "Create profile" : "Edit profile"}
        </Title>
        <Group gap="xs" align="center">
          <Button variant="default" type="button" onClick={requestCancel}>
            Cancel
          </Button>
          <Button type="button" disabled={!isDirty} onClick={handleApply}>
            Apply changes
          </Button>
        </Group>
      </Group>

      <Grid>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Stack gap="lg">
            {issues.length > 0 && (
              <Alert
                color="danger"
                variant="light"
                role="alert"
                title={`${issues.length} issue${issues.length === 1 ? "" : "s"} to fix`}
              >
                Fix the highlighted fields before applying your changes.
              </Alert>
            )}

            <TextInput
              id="profile-name"
              label="Profile name"
              placeholder="e.g. Family viewing"
              autoFocus
              value={draft.name}
              error={nameError}
              onChange={(event) =>
                controller.setName(event.currentTarget.value)
              }
            ></TextInput>

            <section
              className={styles.section}
              aria-labelledby="profile-requirements-heading"
            >
              <Title order={4} id="profile-requirements-heading">
                Subtitle requirements
              </Title>
              <Stack
                gap="sm"
                className={styles.requirements}
                ref={requirementsRef}
              >
                {draft.groups.map((group, index) => (
                  <div
                    key={group.id}
                    className={styles.requirementItem}
                    data-entering={
                      initialGroupIds.has(group.id) ? "false" : "true"
                    }
                    data-exiting={
                      exitingGroupIds.includes(group.id) ? "true" : "false"
                    }
                  >
                    <RequirementCard
                      group={group}
                      index={index}
                      count={draft.groups.length}
                      isBasic={!isEnhanced}
                      isCutoffGroup={isEnhanced && draft.cutoff === group.id}
                      cutoffItemId={isEnhanced ? null : draft.cutoff}
                      languageData={languageData}
                      resolveLanguageName={resolveLanguageName}
                      issues={issuesForGroup(group.id)}
                      onOperator={(operator) =>
                        controller.setGroupOperator(group.id, operator)
                      }
                      onMove={(direction) => handleMoveGroup(group, direction)}
                      onRemoveGroup={() => requestRemoveGroup(group)}
                      onToggleCutoff={() => toggleGroupCutoff(group.id)}
                      onAddItem={() => controller.addItem(group.id)}
                      onUpdateItem={(itemId, patch) =>
                        controller.updateItem(group.id, itemId, patch)
                      }
                      onRemoveItem={(itemId) => handleRemoveItem(group, itemId)}
                      onToggleItemCutoff={toggleItemCutoff}
                    ></RequirementCard>
                  </div>
                ))}
              </Stack>
              {requirementError && (
                <Text size="xs" c="var(--mantine-color-error)">
                  {requirementError}
                </Text>
              )}
              {isEnhanced && (
                <Button
                  id="profile-requirements"
                  variant="default"
                  fullWidth
                  className={styles.dashedButton}
                  leftSection={<FontAwesomeIcon icon={faPlus} />}
                  onClick={controller.addGroup}
                >
                  Add another requirement
                </Button>
              )}
            </section>

            <SearchCompletion
              isEnhanced={isEnhanced}
              cutoff={draft.cutoff}
              groups={draft.groups}
              items={isEnhanced ? [] : (draft.groups[0]?.items ?? [])}
              resolveLanguageName={resolveLanguageName}
              onChange={controller.setCutoff}
              notice={controller.cutoffResetNotice}
              onDismissNotice={controller.dismissCutoffResetNotice}
            ></SearchCompletion>

            <AdvancedSettings
              tag={draft.tag}
              mustContain={draft.mustContain}
              mustNotContain={draft.mustNotContain}
              originalFormat={draft.originalFormat}
              tagError={tagError}
              onTagChange={controller.setTag}
              onMustContainChange={controller.setMustContain}
              onMustNotContainChange={controller.setMustNotContain}
              onOriginalFormatChange={controller.setOriginalFormat}
            ></AdvancedSettings>
          </Stack>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 4 }}>
          <div className={styles.summaryPanel}>
            <ProfileSummary
              summary={summary}
              highlightedRequirementIndex={highlightedRequirementIndex}
            ></ProfileSummary>
          </div>
        </Grid.Col>
      </Grid>
    </Stack>
  );
};

export default ProfileEditor;
