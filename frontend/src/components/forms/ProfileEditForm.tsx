import {
  Action,
  MultiSelector,
  Selector,
  SelectorOption,
  SimpleTable,
} from "@/components";
import { useModals, withModal } from "@/modules/modals";
import { useSelectorOptions } from "@/utilities";
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
import {
  createContext,
  FunctionComponent,
  useCallback,
  useContext,
  useMemo,
} from "react";
import { Column } from "react-table";

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

type ModifyFn = (index: number, item?: Language.ProfileItem) => void;

const RowContext = createContext<ModifyFn>(() => {
  throw new Error("RowContext not initialized");
});

function useRowMutation() {
  return useContext(RowContext);
}

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
    form.values.mustContain ?? [],
    (v) => v
  );

  const mustNotContainOptions = useSelectorOptions(
    form.values.mustNotContain ?? [],
    (v) => v
  );

  const mutation = useCallback(
    (index: number, item?: Language.ProfileItem) => {
      const list = [...form.values.items];
      if (item) {
        list[index] = item;
      } else {
        list.splice(index, 1);
      }
      form.setValues((values) => ({ ...values, items: list }));
    },
    [form]
  );

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
        Cell: ({ value, row }) => {
          const code = value;
          const item = row.original;
          const lang = useMemo(
            () =>
              languageOptions.options.find((l) => l.value.code2 === code)
                ?.value ?? null,
            [code]
          );
          const mutate = useRowMutation();
          return (
            <Selector
              {...languageOptions}
              value={lang}
              onChange={(l) => {
                if (l) {
                  item.language = l.code2;
                  mutate(row.index, item);
                }
              }}
            ></Selector>
          );
        },
      },
      {
        Header: "Forced",
        accessor: "forced",
        Cell: ({ row, value }) => {
          const item = row.original;
          const mutate = useRowMutation();
          return (
            <Checkbox
              checked={value === "True"}
              onChange={(v) => {
                item.forced = v.target.checked ? "True" : "False";
                mutate(row.index, item);
              }}
            ></Checkbox>
          );
        },
      },
      {
        Header: "HI",
        accessor: "hi",
        Cell: ({ row, value }) => {
          const item = row.original;
          const mutate = useRowMutation();
          return (
            <Checkbox
              checked={value === "True"}
              onChange={(v) => {
                item.hi = v.target.checked ? "True" : "False";
                mutate(row.index, item);
              }}
            ></Checkbox>
          );
        },
      },
      {
        Header: "Exclude Audio",
        accessor: "audio_exclude",
        Cell: ({ row, value }) => {
          const item = row.original;
          const mutate = useRowMutation();
          return (
            <Checkbox
              checked={value === "True"}
              onChange={(v) => {
                item.audio_exclude = v.target.checked ? "True" : "False";
                mutate(row.index, item);
              }}
            ></Checkbox>
          );
        },
      },
      {
        id: "action",
        accessor: "id",
        Cell: ({ row }) => {
          const mutate = useRowMutation();
          return (
            <Action icon={faTrash} onClick={() => mutate(row.index)}></Action>
          );
        },
      },
    ],
    [languageOptions]
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
        >
          <Accordion.Item label="Languages">
            <Stack>
              {form.errors.items}
              <RowContext.Provider value={mutation}>
                <SimpleTable
                  columns={columns}
                  data={form.values.items}
                ></SimpleTable>
              </RowContext.Provider>
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
              <MultiSelector
                creatable
                searchable
                label="Must contain"
                {...mustContainOptions}
                {...form.getInputProps("mustContain")}
                getCreateLabel={(query) => `Add "${query}"`}
                onCreate={(query) => {
                  form.setValues((values) => ({
                    ...values,
                    mustContain: [...(values.mustContain ?? []), query],
                  }));
                }}
              ></MultiSelector>
              <Text size="sm">
                Subtitles release info must include one of those words or they
                will be excluded from search results (regex supported).
              </Text>
              <MultiSelector
                creatable
                searchable
                label="Must not contain"
                {...mustNotContainOptions}
                {...form.getInputProps("mustNotContain")}
                getCreateLabel={(query) => `Add "${query}"`}
                onCreate={(query) => {
                  form.setValues((values) => ({
                    ...values,
                    mustNotContain: [...(values.mustNotContain ?? []), query],
                  }));
                }}
              ></MultiSelector>
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
