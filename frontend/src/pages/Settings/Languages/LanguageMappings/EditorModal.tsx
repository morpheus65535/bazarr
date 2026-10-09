import { FunctionComponent, useMemo } from "react";
import {
  Alert,
  Button,
  Code,
  Group,
  Radio,
  SegmentedControl,
  Select,
  SimpleGrid,
  Stack,
  Text,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import {
  faArrowRightArrowLeft,
  faClosedCaptioning,
  faLanguage,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useModals, withModal } from "@/modules/modals";
import {
  createLanguageAliasRules,
  createSubtitleFallbackRule,
  encodeLanguageMapping,
  LanguageMappingPurpose,
  LanguageMappingRule,
  LanguageMappingVariant,
  languageMappingVariantLabel,
  RawRuleRef,
  validateLanguageMappingBatch,
} from "./model";
import styles from "./EditorModal.module.scss";

interface FormValues {
  purpose: LanguageMappingPurpose;
  targetCode: string;
  targetVariant: LanguageMappingVariant;
  sourceCode: string;
  sourceVariant: LanguageMappingVariant;
  fallbackVariant: "hi" | "forced";
}

interface Props {
  languages: Language.Server[];
  targetLanguages: Language.Server[];
  rawRules: string[];
  editingRefs?: RawRuleRef[];
  initialPurpose?: LanguageMappingPurpose;
  initialRule?: LanguageMappingRule;
  onComplete: (encodedRules: string[]) => void;
}

const purposeOptions = [
  {
    value: "language-alias",
    icon: faLanguage,
    title: "Language alias",
    description:
      "Accept one language as an enabled one. Standard, HI, and Forced subtitle types stay unchanged.",
    example: "Spanish (Latino) → Spanish",
  },
  {
    value: "subtitle-type-fallback",
    icon: faClosedCaptioning,
    title: "Subtitle-type fallback",
    description:
      "Allow a specialized subtitle type to satisfy a standard request for the same language.",
    example: "English HI → English",
  },
  {
    value: "advanced-exact",
    icon: faWrench,
    title: "Advanced exact mapping",
    description:
      "Configure an exact source language and subtitle type, and the target it becomes.",
    example: "Any language and type → any enabled language and type",
  },
];
const variantOptions = [
  { label: "Standard", value: "standard" },
  { label: "HI", value: "hi" },
  { label: "Forced", value: "forced" },
];

const Editor: FunctionComponent<Props> = ({
  languages,
  targetLanguages,
  rawRules,
  editingRefs = [],
  initialPurpose = "language-alias",
  initialRule,
  onComplete,
}) => {
  const modals = useModals();
  const form = useForm<FormValues>({
    initialValues: {
      purpose: initialPurpose,
      targetCode: initialRule?.target.code ?? "",
      targetVariant: initialRule?.target.variant ?? "standard",
      sourceCode: initialRule?.source.code ?? "",
      sourceVariant: initialRule?.source.variant ?? "standard",
      fallbackVariant:
        initialRule?.source.variant === "forced" ? "forced" : "hi",
    },
  });

  const languageOptions = useMemo(
    () => languages.map(({ code3: value, name: label }) => ({ value, label })),
    [languages],
  );
  const targetOptions = useMemo(
    () =>
      targetLanguages.map(({ code3: value, name: label }) => ({
        value,
        label,
      })),
    [targetLanguages],
  );
  const sourceLanguage = languages.find(
    (language) => language.code3 === form.values.sourceCode,
  );
  const targetLanguage = languages.find(
    (language) => language.code3 === form.values.targetCode,
  );
  const targetEnabled = targetLanguages.some(
    (language) => language.code3 === form.values.targetCode,
  );

  const candidates = useMemo<LanguageMappingRule[]>(() => {
    if (!targetLanguage) return [];
    if (form.values.purpose === "subtitle-type-fallback") {
      return [
        createSubtitleFallbackRule(
          targetLanguage.code3,
          form.values.fallbackVariant,
        ),
      ];
    }
    if (!sourceLanguage) return [];
    if (form.values.purpose === "language-alias") {
      return createLanguageAliasRules(
        sourceLanguage.code3,
        targetLanguage.code3,
      );
    }
    return [
      {
        source: {
          code: sourceLanguage.code3,
          variant: form.values.sourceVariant,
        },
        target: {
          code: targetLanguage.code3,
          variant: form.values.targetVariant,
        },
      },
    ];
  }, [form.values, sourceLanguage, targetLanguage]);

  const validationError =
    candidates.length > 0
      ? validateLanguageMappingBatch(
          candidates,
          rawRules,
          languages,
          editingRefs,
        )
      : undefined;
  const targetError =
    form.values.targetCode && !targetEnabled
      ? "The canonical target must be enabled in Languages Filter."
      : undefined;
  const canConfirm = candidates.length > 0 && !validationError && !targetError;
  const encodedRules = candidates.map(encodeLanguageMapping);
  const isEditing = editingRefs.length > 0;

  return (
    <form
      onSubmit={form.onSubmit(() => {
        if (!canConfirm) return;
        onComplete(encodedRules);
        modals.closeSelf();
      })}
    >
      <Stack gap="md">
        <div>
          <Text fw={600} mb={4}>
            What do you want to accomplish?
          </Text>
          <Text size="sm" c="dimmed" mb="md">
            Language aliases preserve Standard, HI, and Forced subtitle types
            automatically. Use Advanced only for an exact conversion.
          </Text>
          <Radio.Group
            name="mapping-purpose"
            value={form.values.purpose}
            disabled={isEditing}
            onChange={(value) =>
              form.setFieldValue(
                "purpose",
                (value ?? "language-alias") as LanguageMappingPurpose,
              )
            }
          >
            <SimpleGrid cols={{ base: 1, lg: 3 }}>
              {purposeOptions.map((option) => (
                <Radio.Card
                  key={option.value}
                  value={option.value}
                  className={styles.purposeCard}
                  p="sm"
                >
                  <Group wrap="nowrap" align="flex-start" gap="sm">
                    <Radio.Indicator />
                    <Stack gap={4}>
                      <Group gap={6} align="center" wrap="nowrap">
                        <FontAwesomeIcon
                          icon={option.icon}
                          size="xs"
                          aria-hidden
                        />
                        <Text size="sm" fw={600}>
                          {option.title}
                        </Text>
                      </Group>
                      <Text size="xs" c="dimmed">
                        {option.description}
                      </Text>
                      <Text size="xs" c="dimmed" fs="italic">
                        {option.example}
                      </Text>
                    </Stack>
                  </Group>
                </Radio.Card>
              ))}
            </SimpleGrid>
          </Radio.Group>
        </div>

        <Stack gap="xs">
          <Text fw={600}>1. Canonical target</Text>
          <Text size="sm" c="dimmed">
            Which enabled language does your profile request?
          </Text>
          <Select
            searchable
            label="Canonical language"
            placeholder="Select an enabled language"
            data={targetOptions}
            value={form.values.targetCode || null}
            onChange={(value) => form.setFieldValue("targetCode", value ?? "")}
            error={targetError}
          />
          {form.values.purpose === "advanced-exact" ? (
            <SegmentedControl
              fullWidth
              aria-label="Target subtitle type"
              data={variantOptions}
              value={form.values.targetVariant}
              onChange={(value) =>
                form.setFieldValue(
                  "targetVariant",
                  value as LanguageMappingVariant,
                )
              }
            />
          ) : null}
        </Stack>

        {form.values.purpose !== "subtitle-type-fallback" ? (
          <Button
            fullWidth
            variant="light"
            leftSection={
              <FontAwesomeIcon icon={faArrowRightArrowLeft} size="sm" />
            }
            disabled={!form.values.sourceCode}
            onClick={() => {
              const { targetCode, targetVariant, sourceCode, sourceVariant } =
                form.values;
              form.setValues({
                targetCode: sourceCode,
                sourceCode: targetCode,
                targetVariant: sourceVariant,
                sourceVariant: targetVariant,
              });
            }}
          >
            Swap target and source
          </Button>
        ) : null}

        {form.values.purpose === "subtitle-type-fallback" ? (
          <Stack gap="xs">
            <Text fw={600}>2. Accepted subtitle type</Text>
            <Text size="sm" c="dimmed">
              Allow this type to satisfy a Standard request for the same
              language.
            </Text>
            <SegmentedControl
              fullWidth
              aria-label="Accepted subtitle type"
              data={[
                { label: "Hearing impaired", value: "hi" },
                { label: "Forced", value: "forced" },
              ]}
              value={form.values.fallbackVariant}
              onChange={(value) =>
                form.setFieldValue("fallbackVariant", value as "hi" | "forced")
              }
            />
          </Stack>
        ) : (
          <Stack gap="xs">
            <Text fw={600}>2. Accepted source</Text>
            <Text size="sm" c="dimmed">
              What language might a provider or embedded track report instead?
            </Text>
            <Select
              searchable
              label="Provider or track language"
              placeholder="Select any known language"
              data={languageOptions}
              value={form.values.sourceCode || null}
              disabled={!form.values.targetCode}
              onChange={(value) =>
                form.setFieldValue("sourceCode", value ?? "")
              }
            />
            {form.values.purpose === "advanced-exact" ? (
              <SegmentedControl
                fullWidth
                aria-label="Source subtitle type"
                data={variantOptions}
                value={form.values.sourceVariant}
                onChange={(value) =>
                  form.setFieldValue(
                    "sourceVariant",
                    value as LanguageMappingVariant,
                  )
                }
              />
            ) : (
              <Text size="xs" c="dimmed">
                Standard, Hearing impaired, and Forced types will each remain
                the same after mapping.
              </Text>
            )}
          </Stack>
        )}

        {candidates.length > 0 ? (
          <Alert
            color={validationError ? "red" : "green"}
            variant="light"
            title={validationError ? "Check this mapping" : "Review the impact"}
          >
            {validationError ? (
              validationError.message
            ) : (
              <Stack gap="xs">
                <Text size="sm">
                  {form.values.purpose === "language-alias" &&
                  sourceLanguage &&
                  targetLanguage
                    ? `${sourceLanguage.name} will satisfy ${targetLanguage.name} requests while preserving each subtitle type.`
                    : form.values.purpose === "subtitle-type-fallback" &&
                        targetLanguage
                      ? `${languageMappingVariantLabel(form.values.fallbackVariant)} ${targetLanguage.name} will satisfy Standard ${targetLanguage.name} requests.`
                      : "Bazarr will apply this exact source-to-target conversion."}
                </Text>
                {encodedRules.map((encoded) => (
                  <Code key={encoded} block>
                    {encoded}
                  </Code>
                ))}
              </Stack>
            )}
          </Alert>
        ) : null}

        <Group justify="flex-end">
          <Button variant="default" onClick={modals.closeSelf}>
            Cancel
          </Button>
          <Button type="submit" disabled={!canConfirm}>
            {isEditing ? "Update mapping" : "Add mapping"}
          </Button>
        </Group>
      </Stack>
    </form>
  );
};

export const LanguageMappingEditorModal = withModal(
  Editor,
  "language-mapping-editor",
  { title: "Language mapping", size: "xl" },
);
