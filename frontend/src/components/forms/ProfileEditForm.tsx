import { Action, Selector, SelectorOption, SimpleTable } from "@/components";
import { useModals, withModal } from "@/modules/modals";
import { useTableStyles } from "@/styles";
import { useArrayAction, useSelectorOptions } from "@/utilities";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import {
  Accordion,
  Alert,
  Button,
  Checkbox,
  Stack,
  Switch,
  Text,
  TextInput,
} from "@mantine/core";
import { useForm } from "@mantine/hooks";
import { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";
import ChipInput from "../inputs/ChipInput";

export const anyCutoff = 65535;

const defaultCutoffOptions: SelectorOption<Language.ProfileItem>[] = [
  {
    label: "Any",
    value: {
      id: anyCutoff,
      audio_exclude: "False",
      forced: "False",
      hi: "False",
      language: "any",
    },
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
    validationRules: {
      name: (value) => value.length > 0,
      items: (value) => value.length > 0,
    },
    errorMessages: {
      items: (
        <Alert color="yellow" variant="outline">
          Must contain at lease 1 language
        </Alert>
      ),
    },
  });

  const languageOptions = useSelectorOptions(languages, (l) => l.name);

  const itemCutoffOptions = useSelectorOptions(
    form.values.items,
    (v) => v.language
  );

  const cutoffOptions = useMemo(
    () => ({
      ...itemCutoffOptions,
      options: [...itemCutoffOptions.options, ...defaultCutoffOptions],
    }),
    [itemCutoffOptions]
  );

  const mustContainOptions = useSelectorOptions(
    form.values.mustContain,
    (v) => v
  );

  const mustNotContainOptions = useSelectorOptions(
    form.values.mustNotContain,
    (v) => v
  );

  const action = useArrayAction<Language.ProfileItem>((fn) => {
    form.setValues((values) => ({ ...values, items: fn(values.items) }));
  });

  const addItem = useCallback(() => {
    const id =
      1 +
      form.values.items.reduce<number>(
        (val, item) => Math.max(item.id, val),
        0
      );

    if (languages.length > 0) {
      const language = languages[0].code2;

      const item: Language.ProfileItem = {
        id,
        language,
        audio_exclude: "False",
        hi: "False",
        forced: "False",
      };

      const list = [...form.values.items, item];
      form.setValues((values) => ({ ...values, items: list }));
    }
  }, [form, languages]);

  const columns = useMemo<Column<Language.ProfileItem>[]>(
    () => [
      {
        Header: "ID",
        accessor: "id",
      },
      {
        Header: "Language",
        accessor: "language",
        Cell: ({ value: code, row: { original: item, index } }) => {
          const language = useMemo(
            () =>
              languageOptions.options.find((l) => l.value.code2 === code)
                ?.value ?? null,
            [code]
          );

          const { classes } = useTableStyles();

          return (
            <Selector
              {...languageOptions}
              className={classes.select}
              value={language}
              onChange={(value) => {
                if (value) {
                  item.language = value.code2;
                  action.mutate(index, { ...item, language: value.code2 });
                }
              }}
            ></Selector>
          );
        },
      },
      {
        Header: "Forced",
        accessor: "forced",
        Cell: ({ row: { original: item, index }, value }) => {
          return (
            <Checkbox
              checked={value === "True"}
              onChange={({ currentTarget: { checked } }) => {
                action.mutate(index, {
                  ...item,
                  forced: checked ? "True" : "False",
                  hi: checked ? "False" : item.hi,
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        Header: "HI",
        accessor: "hi",
        Cell: ({ row: { original: item, index }, value }) => {
          return (
            <Checkbox
              checked={value === "True"}
              onChange={({ currentTarget: { checked } }) => {
                action.mutate(index, {
                  ...item,
                  hi: checked ? "True" : "False",
                  forced: checked ? "False" : item.forced,
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        Header: "Exclude Audio",
        accessor: "audio_exclude",
        Cell: ({ row: { original: item, index }, value }) => {
          return (
            <Checkbox
              checked={value === "True"}
              onChange={({ currentTarget: { checked } }) => {
                action.mutate(index, {
                  ...item,
                  audio_exclude: checked ? "True" : "False",
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        id: "action",
        accessor: "id",
        Cell: ({ row }) => {
          return (
            <Action
              icon={faTrash}
              color="red"
              onClick={() => action.remove(row.index)}
            ></Action>
          );
        },
      },
    ],
    [action, languageOptions]
  );

  return (
    <form
      onSubmit={form.onSubmit((value) => {
        onComplete?.(value);
        modals.closeSelf();
      })}
    >
      <Stack>
        <TextInput label="Name" {...form.getInputProps("name")}></TextInput>
        <Accordion
          offsetIcon={false}
          multiple
          iconPosition="right"
          initialItem={0}
          styles={(theme) => ({
            contentInner: {
              [theme.fn.smallerThan("md")]: {
                padding: 0,
              },
            },
          })}
        >
          <Accordion.Item label="Languages">
            <Stack>
              {form.errors.items}
              <SimpleTable
                columns={columns}
                data={form.values.items}
              ></SimpleTable>
              <Button fullWidth color="light" onClick={addItem}>
                Add Language
              </Button>
              <Selector
                clearable
                label="Cutoff"
                {...cutoffOptions}
                {...form.getInputProps("cutoff")}
              ></Selector>
            </Stack>
          </Accordion.Item>
          <Accordion.Item label="Release Info">
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
          <Accordion.Item label="Subtitles">
            <Stack my="xs">
              <Switch
                label="Use Original Format"
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
    size: "lg",
  }
);

export default ProfileEditForm;
