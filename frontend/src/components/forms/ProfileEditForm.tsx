import React, { FunctionComponent, useCallback, useMemo } from "react";
import {
  Accordion,
  Button,
  Flex,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { ColumnDef } from "@tanstack/react-table";
import { Action, Selector, SelectorOption } from "@/components";
import ChipInput from "@/components/inputs/ChipInput";
import SimpleTable from "@/components/tables/SimpleTable";
import { useModals, withModal } from "@/modules/modals";
import { useArrayAction, useSelectorOptions } from "@/utilities";
import { LOG } from "@/utilities/console";
import FormUtils from "@/utilities/form";
import styles from "./ProfileEditForm.module.scss";

export const anyCutoff = 65535;

const defaultCutoffOptions: SelectorOption<Language.ProfileItem>[] = [
  {
    label: "Any",
    value: {
      id: anyCutoff,
      // eslint-disable-next-line camelcase
      audio_exclude: "False",
      // eslint-disable-next-line camelcase
      audio_only_include: "False",
      forced: "False",
      hi: "False",
      language: "any",
    },
  },
];

const subtitlesTypeOptions: SelectorOption<string>[] = [
  {
    label: "Normal or hearing-impaired",
    value: "normal",
  },
  {
    label: "Hearing-impaired required",
    value: "hi",
  },
  {
    label: "Forced (foreign part only)",
    value: "forced",
  },
];

const inclusionOptions: SelectorOption<string>[] = [
  {
    label: "Always",
    value: "always_include",
  },
  {
    label: "audio track matches",
    value: "audio_only_include",
  },
  {
    label: "no audio track matches",
    value: "audio_exclude",
  },
];

interface Props {
  onComplete?: (profile: Language.Profile) => void;
  languages: readonly Language.Info[];
  profile: Language.Profile;
}

const ProfileEditForm: FunctionComponent<Props> = ({
  onComplete,
  languages,
  profile,
}) => {
  const modals = useModals();

  const form = useForm({
    initialValues: profile,
    validate: {
      name: FormUtils.validation(
        (value: string) => value.length > 0,
        "Must have a name",
      ),
      tag: FormUtils.validation((value: string | undefined) => {
        if (!value) {
          return true;
        }

        return /^[a-z_0-9-]+$/.test(value);
      }, "Only lowercase alphanumeric characters, underscores (_) and hyphens (-) are allowed"),
      items: FormUtils.validation(
        (value: Language.ProfileItem[]) => value.length > 0,
        "Must contain at least 1 language",
      ),
    },
  });

  const languageOptions = useSelectorOptions(languages, (l) => l.name);

  const itemCutoffOptions = useSelectorOptions(
    form.values.items,
    (v) => {
      const suffix =
        v.hi === "True" ? ":hi" : v.forced === "True" ? ":forced" : "";

      return v.language + suffix;
    },
    (v) => String(v.id),
  );

  const cutoffOptions = useMemo(
    () => ({
      ...itemCutoffOptions,
      options: [...itemCutoffOptions.options, ...defaultCutoffOptions],
    }),
    [itemCutoffOptions],
  );

  const selectedCutoff = useMemo(
    () =>
      cutoffOptions.options.find((v) => v.value.id === form.values.cutoff)
        ?.value ?? null,
    [cutoffOptions, form.values.cutoff],
  );

  const mustContainOptions = useSelectorOptions(
    form.values.mustContain,
    (v) => v,
  );

  const mustNotContainOptions = useSelectorOptions(
    form.values.mustNotContain,
    (v) => v,
  );

  const action = useArrayAction<Language.ProfileItem>((fn) => {
    form.setValues((values) => ({ ...values, items: fn(values.items ?? []) }));
  });

  const addItem = useCallback(() => {
    const id =
      1 +
      form.values.items.reduce<number>(
        (val, item) => Math.max(item.id, val),
        0,
      );

    if (languages.length > 0) {
      const language = languages[0].code2;

      const item: Language.ProfileItem = {
        id,
        language,
        // eslint-disable-next-line camelcase
        audio_exclude: "False",
        // eslint-disable-next-line camelcase
        audio_only_include: "False",
        hi: "False",
        forced: "False",
      };

      const list = [...form.values.items, item];
      form.setValues((values) => ({ ...values, items: list }));
    }
  }, [form, languages]);

  const LanguageCell = React.memo(
    ({ item, index }: { item: Language.ProfileItem; index: number }) => {
      const code = useMemo(
        () =>
          languageOptions.options.find((l) => l.value.code2 === item.language)
            ?.value ?? null,
        [item.language],
      );

      return (
        <Selector
          {...languageOptions}
          className="table-select"
          value={code}
          onChange={(value) => {
            if (value) {
              item.language = value.code2;
              action.mutate(index, { ...item, language: value.code2 });
            }
          }}
        ></Selector>
      );
    },
  );

  const SubtitleTypeCell = React.memo(
    ({ item, index }: { item: Language.ProfileItem; index: number }) => {
      const selectValue = useMemo(() => {
        if (item.forced === "True") {
          return "forced";
        } else if (item.hi === "True") {
          return "hi";
        } else {
          return "normal";
        }
      }, [item.forced, item.hi]);

      return (
        <Select
          value={selectValue}
          data={subtitlesTypeOptions}
          onChange={(value) => {
            if (value) {
              action.mutate(index, {
                ...item,
                hi: value === "hi" ? "True" : "False",
                forced: value === "forced" ? "True" : "False",
              });
            }
          }}
        ></Select>
      );
    },
  );

  const InclusionCell = React.memo(
    ({ item, index }: { item: Language.ProfileItem; index: number }) => {
      const selectValue = useMemo(() => {
        if (item.audio_exclude === "True") {
          return "audio_exclude";
        } else if (item.audio_only_include === "True") {
          return "audio_only_include";
        } else {
          return "always_include";
        }
      }, [item.audio_exclude, item.audio_only_include]);

      return (
        <Select
          value={selectValue}
          data={inclusionOptions}
          onChange={(value) => {
            if (value) {
              action.mutate(index, {
                ...item,
                // eslint-disable-next-line camelcase
                audio_exclude: value === "audio_exclude" ? "True" : "False",
                // eslint-disable-next-line camelcase
                audio_only_include:
                  value === "audio_only_include" ? "True" : "False",
              });
            }
          }}
        ></Select>
      );
    },
  );

  const columns = useMemo<ColumnDef<Language.ProfileItem>[]>(
    () => [
      {
        header: "ID",
        accessorKey: "id",
      },
      {
        header: "Language",
        accessorKey: "language",
        cell: ({ row: { original: item, index } }) => {
          return <LanguageCell item={item} index={index} />;
        },
      },
      {
        header: "Subtitles Type",
        accessorKey: "forced",
        cell: ({ row: { original: item, index } }) => {
          return <SubtitleTypeCell item={item} index={index} />;
        },
      },
      {
        header: "Search only when...",
        accessorKey: "audio_exclude",
        cell: ({ row: { original: item, index } }) => {
          return <InclusionCell item={item} index={index} />;
        },
      },
      {
        id: "action",
        cell: ({ row }) => {
          return (
            <Action
              label="Remove"
              icon={faTrash}
              c="red"
              onClick={() => action.remove(row.index)}
            ></Action>
          );
        },
      },
    ],
    [action, LanguageCell, SubtitleTypeCell, InclusionCell],
  );

  return (
    <form
      onSubmit={form.onSubmit((value) => {
        LOG("info", "Submitting language profile", value);
        onComplete?.(value);
        modals.closeSelf();
      })}
    >
      <Stack>
        <Flex
          direction={{ base: "column", sm: "row" }}
          gap="sm"
          className={styles.evenly}
        >
          <TextInput label="Name" {...form.getInputProps("name")}></TextInput>
          <TextInput
            label="Tag"
            {...form.getInputProps("tag")}
            onBlur={() =>
              form.setFieldValue(
                "tag",
                (prev) =>
                  prev?.toLowerCase().trim().replace(/\s+/g, "_") ?? undefined,
              )
            }
          ></TextInput>
        </Flex>
        <Accordion
          multiple
          chevronPosition="right"
          defaultValue={["Languages"]}
          className={styles.content}
        >
          <Accordion.Item value="Languages">
            <Stack>
              <SimpleTable
                columns={columns}
                data={form.values.items}
              ></SimpleTable>
              <Button fullWidth onClick={addItem}>
                Add Language
              </Button>
              <Text c="var(--mantine-color-error)">{form.errors.items}</Text>
              <Selector
                clearable
                label="Cutoff"
                {...cutoffOptions}
                value={selectedCutoff}
                onChange={(value) => {
                  form.setFieldValue("cutoff", value?.id ?? null);
                }}
              ></Selector>
            </Stack>
          </Accordion.Item>
          <Accordion.Item value="Release Info">
            <Stack>
              <ChipInput
                label="Must contain"
                {...mustContainOptions}
                {...form.getInputProps("mustContain")}
              ></ChipInput>
              <Text size="sm">
                Subtitles release info must include one of those words or they
                will be excluded from search results (regex supported).
              </Text>
              <ChipInput
                label="Must not contain"
                {...mustNotContainOptions}
                {...form.getInputProps("mustNotContain")}
              ></ChipInput>
              <Text size="sm">
                Subtitles release info including one of those words (case
                insensitive) will be excluded from search results (regex
                supported).
              </Text>
            </Stack>
          </Accordion.Item>
          <Accordion.Item value="Subtitles">
            <Stack my="xs">
              <Switch
                label="Use Original Format"
                checked={form.values.originalFormat ?? false}
                {...form.getInputProps("originalFormat")}
              ></Switch>
              <Text size="sm">
                Download subtitle file without format conversion
              </Text>
            </Stack>
          </Accordion.Item>
        </Accordion>
        <Button type="submit">Save</Button>
      </Stack>
    </form>
  );
};

export const ProfileEditModal = withModal(
  ProfileEditForm,
  "languages-profile-editor",
  {
    title: "Edit Languages Profile",
    size: "xl",
  },
);
