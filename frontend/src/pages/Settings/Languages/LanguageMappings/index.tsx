import { FunctionComponent, useCallback, useMemo } from "react";
import {
  Accordion,
  Alert,
  Badge,
  Button,
  Card,
  Code,
  Group,
  List,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Title,
} from "@mantine/core";
import {
  faArrowRight,
  faPen,
  faPlus,
  faTrash,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useLanguages } from "@/apis/hooks";
import { Action } from "@/components";
import { useModals } from "@/modules/modals";
import { languageEqualsKey } from "@/pages/Settings/keys";
import { useLatestEnabledLanguages } from "@/pages/Settings/Languages/useLatestLanguages";
import { useFormActions } from "@/pages/Settings/utilities/FormValues";
import { useSettingValue } from "@/pages/Settings/utilities/hooks";
import { LanguageMappingEditorModal } from "./EditorModal";
import {
  applyRuleSet,
  buildLanguageMappingView,
  getParsedLanguageMappings,
  LanguageMappingEntry,
  languageMappingPresets,
  LanguageMappingPurpose,
  LanguageMappingRule,
  languageMappingVariantLabel,
  normalizeLanguageMappingRule,
  RawRuleRef,
  removeRuleSet,
  validateLanguageMapping,
} from "./model";

const unresolvedReason = (
  entry: Extract<LanguageMappingEntry, { kind: "unresolved" }>,
) => {
  switch (entry.reason) {
    case "unknown-source":
      return "The source language is not available in the current language list.";
    case "unknown-target":
      return "The target language is not available in the current language list.";
    case "unknown-languages":
      return "Neither language is available in the current language list.";
    default:
      return "This value does not use the expected source:target format.";
  }
};

const LanguageMappings: FunctionComponent = () => {
  const { data: languages, error: languagesError, isLoading } = useLanguages();
  const enabledLanguages = useLatestEnabledLanguages();
  const configuredRules = useSettingValue<string[]>(languageEqualsKey, {
    defaultValue: [],
  });
  const rawRules = useMemo(() => configuredRules ?? [], [configuredRules]);
  const { setValue } = useFormActions();
  const modals = useModals();

  const knownLanguages = useMemo(() => languages ?? [], [languages]);
  const enabledCode2 = useMemo(
    () => new Set(enabledLanguages.map((language) => language.code2)),
    [enabledLanguages],
  );
  const targetLanguages = useMemo(
    () => knownLanguages.filter((language) => enabledCode2.has(language.code2)),
    [enabledCode2, knownLanguages],
  );
  const entries = useMemo(
    () => buildLanguageMappingView(rawRules, knownLanguages),
    [knownLanguages, rawRules],
  );

  const setRawRules = useCallback(
    (next: string[]) => setValue(next, languageEqualsKey),
    [setValue],
  );

  const openEditor = useCallback(
    (
      options: {
        refs?: RawRuleRef[];
        purpose?: LanguageMappingPurpose;
        initialRule?: LanguageMappingRule;
      } = {},
    ) => {
      const refs = options.refs ?? [];
      modals.openContextModal(LanguageMappingEditorModal, {
        languages: [...knownLanguages],
        targetLanguages: [...targetLanguages],
        rawRules: [...rawRules],
        editingRefs: refs,
        initialPurpose: options.purpose,
        initialRule: options.initialRule,
        onComplete: (encodedRules) => {
          const next = applyRuleSet(rawRules, refs, encodedRules);
          if (next) setRawRules(next);
        },
      });
    },
    [knownLanguages, modals, rawRules, setRawRules, targetLanguages],
  );

  const remove = useCallback(
    (refs: RawRuleRef[], label: string) => {
      modals.openConfirmModal({
        title: "Remove language mapping?",
        children: (
          <Text size="sm">
            Remove <strong>{label}</strong>? The change will remain pending
            until you save the settings page.
          </Text>
        ),
        labels: { confirm: "Remove", cancel: "Cancel" },
        confirmProps: { color: "danger" },
        onConfirm: () => {
          const next = removeRuleSet(rawRules, refs);
          if (next) setRawRules(next);
        },
      });
    },
    [modals, rawRules, setRawRules],
  );

  const availablePresets = useMemo(
    () =>
      languageMappingPresets.flatMap((preset) => {
        const source = knownLanguages.find(
          (language) => language.code3 === preset.source,
        );
        const target = knownLanguages.find(
          (language) => language.code3 === preset.target,
        );
        if (!source || !target) return [];
        const applied = entries.some(
          (entry) =>
            entry.kind === "language-alias" &&
            entry.sourceLanguage.code3 === preset.source &&
            entry.targetLanguage.code3 === preset.target,
        );
        const matchingVariants = new Set(
          getParsedLanguageMappings(rawRules)
            .map((rule) => normalizeLanguageMappingRule(rule, knownLanguages))
            .filter(
              (rule) =>
                rule.source.code === preset.source &&
                rule.target.code === preset.target &&
                rule.source.variant === rule.target.variant,
            )
            .map((rule) => rule.source.variant),
        );
        return [
          {
            ...preset,
            sourceLanguage: source,
            targetLanguage: target,
            enabled: enabledCode2.has(target.code2),
            applied,
            needsReview: !applied && matchingVariants.size > 0,
          },
        ];
      }),
    [enabledCode2, entries, knownLanguages, rawRules],
  );
  const canAdd = !isLoading && targetLanguages.length > 0;

  if (isLoading && languages === undefined) {
    return <Skeleton height={180} radius="sm" />;
  }

  if (languagesError && languages === undefined) {
    return (
      <Alert color="red" variant="light" title="Languages unavailable">
        Language mappings could not be loaded. Existing settings have not been
        changed.
      </Alert>
    );
  }

  return (
    <Stack gap="md">
      <Alert color="blue" variant="light" title="Mappings are directional">
        A subtitle reported as the source is accepted and treated as the
        canonical target. Mappings do not translate subtitle content and apply
        across providers, existing subtitles, and profile calculations.
      </Alert>

      <Accordion variant="contained">
        <Accordion.Item value="mapping-help">
          <Accordion.Control>How language mappings work</Accordion.Control>
          <Accordion.Panel>
            <Stack gap="sm">
              <div>
                <Text size="sm" fw={600}>
                  Are mappings bidirectional?
                </Text>
                <Text size="sm" c="dimmed">
                  No. Source → target does not also make the target behave as
                  the source.
                </Text>
              </div>
              <div>
                <Text size="sm" fw={600}>
                  Does this translate subtitles?
                </Text>
                <Text size="sm" c="dimmed">
                  No. It only changes how Bazarr searches for and classifies the
                  language.
                </Text>
              </div>
              <div>
                <Text size="sm" fw={600}>
                  Does it affect subtitles I already have?
                </Text>
                <Text size="sm" c="dimmed">
                  Yes. Source subtitles may satisfy target profile requirements
                  and cutoffs, including embedded tracks.
                </Text>
              </div>
              <div>
                <Text size="sm" fw={600}>
                  Can I limit a mapping to one provider?
                </Text>
                <Text size="sm" c="dimmed">
                  No. Mappings apply globally. Do not create one if both
                  languages need to remain distinct.
                </Text>
              </div>
            </Stack>
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>

      {availablePresets.length > 0 ? (
        <Card withBorder padding="md">
          <Stack gap="sm">
            <div>
              <Text fw={600}>Common language aliases</Text>
              <Text size="sm" c="dimmed">
                Start from a reviewed preset, then confirm its impact before
                adding it.
              </Text>
            </div>
            <Group gap="xs">
              {availablePresets.map((preset) => (
                <Button
                  key={`${preset.source}-${preset.target}`}
                  variant="light"
                  disabled={
                    !preset.enabled || preset.applied || preset.needsReview
                  }
                  onClick={() =>
                    openEditor({
                      purpose: "language-alias",
                      initialRule: {
                        source: {
                          code: preset.sourceLanguage.code3,
                          variant: "standard",
                        },
                        target: {
                          code: preset.targetLanguage.code3,
                          variant: "standard",
                        },
                      },
                    })
                  }
                >
                  {preset.label}
                  {preset.applied
                    ? " · Applied"
                    : preset.needsReview
                      ? " · Needs review"
                      : !preset.enabled
                        ? " · Enable target first"
                        : ""}
                </Button>
              ))}
            </Group>
          </Stack>
        </Card>
      ) : null}

      {rawRules.length === 0 ? (
        <Card withBorder padding="lg">
          <Stack gap="md">
            <div>
              <Title order={5}>Accept another language label</Title>
              <Text size="sm" c="dimmed" mt={4}>
                Use a mapping when a provider or embedded track reports an
                acceptable subtitle differently from your language profile.
              </Text>
            </div>

            <Card
              withBorder
              padding="md"
              bg="var(--mantine-color-default-hover)"
            >
              <Group justify="center" gap="md" wrap="wrap">
                <Stack gap={0} align="center">
                  <Text size="xs" c="dimmed">
                    Provider offers
                  </Text>
                  <Text fw={600}>Spanish (Latino)</Text>
                </Stack>
                <FontAwesomeIcon icon={faArrowRight} aria-hidden />
                <Stack gap={0} align="center">
                  <Text size="xs" c="dimmed">
                    Profile accepts as
                  </Text>
                  <Text fw={600}>Spanish</Text>
                </Stack>
              </Group>
            </Card>

            <List size="sm" spacing="xs">
              <List.Item>
                Choose the enabled language your profile requests.
              </List.Item>
              <List.Item>Choose what a provider or track may report.</List.Item>
              <List.Item>
                Review the effect before adding the mapping.
              </List.Item>
            </List>

            <Button
              leftSection={<FontAwesomeIcon icon={faPlus} />}
              disabled={!canAdd}
              onClick={() => openEditor()}
            >
              {canAdd
                ? "Create guided mapping"
                : "Enable a subtitle language first"}
            </Button>
            {!canAdd && !isLoading ? (
              <Text size="xs" c="dimmed" ta="center">
                Enable a target in Languages Filter above before creating a
                mapping.
              </Text>
            ) : null}
          </Stack>
        </Card>
      ) : (
        <>
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            {entries.map((entry) => {
              if (entry.kind === "language-alias") {
                const label = `${entry.sourceLanguage.name} to ${entry.targetLanguage.name}`;
                const refs = entry.members.map(({ index, raw }) => ({
                  index,
                  raw,
                }));
                const standardRule = entry.members.find(
                  (member) => member.variant === "standard",
                )?.rule;
                const initialRule = standardRule
                  ? normalizeLanguageMappingRule(standardRule, knownLanguages)
                  : undefined;
                return (
                  <Card key={`alias-${entry.index}`} withBorder padding="md">
                    <Stack gap="sm">
                      <Group
                        justify="space-between"
                        align="flex-start"
                        wrap="wrap"
                      >
                        <Group gap="sm">
                          <Text fw={600}>{entry.sourceLanguage.name}</Text>
                          <FontAwesomeIcon icon={faArrowRight} aria-hidden />
                          <Text fw={600}>{entry.targetLanguage.name}</Text>
                        </Group>
                        <Group gap="xs">
                          <Action
                            label={`Edit alias ${label}`}
                            icon={faPen}
                            c="secondary"
                            onClick={() =>
                              openEditor({
                                refs,
                                purpose: "language-alias",
                                initialRule,
                              })
                            }
                          />
                          <Action
                            label={`Remove alias ${label}`}
                            icon={faTrash}
                            c="danger"
                            onClick={() => remove(refs, label)}
                          />
                        </Group>
                      </Group>
                      <Badge variant="light" color="brand">
                        Preserves Standard, HI, and Forced types
                      </Badge>
                      <Text size="sm">
                        When <strong>{entry.targetLanguage.name}</strong> is
                        requested, Bazarr can accept{" "}
                        <strong>{entry.sourceLanguage.name}</strong> while
                        preserving the subtitle type.
                      </Text>
                    </Stack>
                  </Card>
                );
              }

              if (entry.kind === "unresolved") {
                return (
                  <Card
                    key={`${entry.index}-${entry.raw}`}
                    withBorder
                    padding="md"
                  >
                    <Stack gap="sm">
                      <Group justify="space-between" align="flex-start">
                        <div>
                          <Badge color="warning" variant="light">
                            Needs attention
                          </Badge>
                          <Text fw={600} mt="xs">
                            Unresolved mapping
                          </Text>
                        </div>
                        <Group gap="xs">
                          <Action
                            label={`Repair mapping ${entry.raw}`}
                            icon={faWrench}
                            c="secondary"
                            onClick={() =>
                              openEditor({
                                refs: [{ index: entry.index, raw: entry.raw }],
                                purpose: "advanced-exact",
                              })
                            }
                          />
                          <Action
                            label={`Remove mapping ${entry.raw}`}
                            icon={faTrash}
                            c="danger"
                            onClick={() =>
                              remove(
                                [{ index: entry.index, raw: entry.raw }],
                                entry.raw,
                              )
                            }
                          />
                        </Group>
                      </Group>
                      <Code block>{entry.raw}</Code>
                      <Text size="sm" c="dimmed">
                        {unresolvedReason(entry)} It will be preserved unchanged
                        until you repair or remove it.
                      </Text>
                    </Stack>
                  </Card>
                );
              }

              const normalizedRule: LanguageMappingRule = {
                source: {
                  ...entry.rule.source,
                  code: entry.sourceLanguage.code3,
                },
                target: {
                  ...entry.rule.target,
                  code: entry.targetLanguage.code3,
                },
              };
              const otherRules = getParsedLanguageMappings(
                rawRules.filter((_, index) => index !== entry.index),
              ).map((rule) =>
                normalizeLanguageMappingRule(rule, knownLanguages),
              );
              const legacyWarning = validateLanguageMapping(
                normalizedRule,
                otherRules,
              );
              const targetEnabled = enabledCode2.has(
                entry.targetLanguage.code2,
              );
              const label = `${entry.sourceLanguage.name} to ${entry.targetLanguage.name}`;

              return (
                <Card
                  key={`${entry.index}-${entry.raw}`}
                  withBorder
                  padding="md"
                >
                  <Stack gap="sm">
                    <Group
                      justify="space-between"
                      align="flex-start"
                      wrap="wrap"
                    >
                      <Group gap="sm" wrap="wrap">
                        <Stack gap={2}>
                          <Text size="xs" c="dimmed">
                            Provider or track
                          </Text>
                          <Text fw={600}>{entry.sourceLanguage.name}</Text>
                          <Badge size="sm" variant="light" color="secondary">
                            {languageMappingVariantLabel(
                              entry.rule.source.variant,
                            )}
                          </Badge>
                        </Stack>
                        <FontAwesomeIcon icon={faArrowRight} aria-hidden />
                        <Stack gap={2}>
                          <Text size="xs" c="dimmed">
                            Canonical target
                          </Text>
                          <Text fw={600}>{entry.targetLanguage.name}</Text>
                          <Badge size="sm" variant="light" color="brand">
                            {languageMappingVariantLabel(
                              entry.rule.target.variant,
                            )}
                          </Badge>
                        </Stack>
                      </Group>
                      <Group gap="xs" wrap="nowrap">
                        <Action
                          label={`Edit mapping ${label}`}
                          icon={faPen}
                          c="secondary"
                          onClick={() =>
                            openEditor({
                              refs: [{ index: entry.index, raw: entry.raw }],
                              purpose:
                                normalizedRule.source.code ===
                                  normalizedRule.target.code &&
                                normalizedRule.target.variant === "standard" &&
                                normalizedRule.source.variant !== "standard"
                                  ? "subtitle-type-fallback"
                                  : "advanced-exact",
                              initialRule: normalizedRule,
                            })
                          }
                        />
                        <Action
                          label={`Remove mapping ${label}`}
                          icon={faTrash}
                          c="danger"
                          onClick={() =>
                            remove(
                              [{ index: entry.index, raw: entry.raw }],
                              label,
                            )
                          }
                        />
                      </Group>
                    </Group>

                    <Text size="sm">
                      When <strong>{entry.targetLanguage.name}</strong> is
                      requested, Bazarr can accept{" "}
                      <strong>{entry.sourceLanguage.name}</strong> and treat it
                      as the target.
                    </Text>

                    {!targetEnabled || legacyWarning ? (
                      <Alert color="warning" variant="light">
                        {!targetEnabled
                          ? "The canonical target is no longer enabled. Edit this mapping to choose an enabled target."
                          : legacyWarning?.message}
                      </Alert>
                    ) : null}
                  </Stack>
                </Card>
              );
            })}
          </SimpleGrid>

          <Button
            fullWidth
            leftSection={<FontAwesomeIcon icon={faPlus} />}
            disabled={!canAdd}
            onClick={() => openEditor()}
          >
            {canAdd
              ? "Add language mapping"
              : "Enable a subtitle language first"}
          </Button>
        </>
      )}
    </Stack>
  );
};

export default LanguageMappings;
