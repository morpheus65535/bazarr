import { FunctionComponent, useCallback, useMemo } from "react";
import {
  Accordion,
  Button,
  Card,
  Flex,
  Group,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import {
  faArrowDown,
  faArrowUp,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { Action, Selector, SelectorOption } from "@/components";
import ChipInput from "@/components/inputs/ChipInput";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
import SimpleTable from "@/components/tables/SimpleTable";
import { useModals, withModal } from "@/modules/modals";
import { useSelectorOptions } from "@/utilities";
import { LOG } from "@/utilities/console";
import FormUtils from "@/utilities/form";
import { anyCutoff } from "./ProfileEditForm";
import { inclusionOptions, subtitlesTypeOptions } from "./profileOptions";
import styles from "./ProfileEditForm.module.scss";

type Group = Language.EnhancedGroup;
type Item = Language.ProfileItem;

const operatorOptions: SelectorOption<string>[] = [
  { label: "AND", value: "AND" },
  { label: "OR", value: "OR" },
];

const itemLabel = (item: Item) =>
  item.language +
  (item.hi === "True"
    ? ":HI"
    : item.forced === "True"
      ? ":Forced"
      : item.hi === "Excluded"
        ? ":Non-HI"
        : "");

const groupExpression = (group: Group) =>
  group.items.map(itemLabel).join(` ${group.operator} `);

const nextId = (ids: number[]) =>
  1 + ids.reduce<number>((max, id) => Math.max(max, id), 0);

const newItem = (id: number, language: string): Item => ({
  id,
  language,
  audioExclude: "False",
  audioOnlyInclude: "False",
  hi: "False",
  forced: "False",
});

// Same key as the item shape a backend saves: a language cannot repeat with the same subtitle type in one group.
const hasRepeatedLanguage = (items: Item[]) =>
  new Set(items.map((item) => `${item.language}|${item.hi}|${item.forced}`))
    .size !== items.length;

const subtitleTypeValue = (item: Item) => {
  if (item.forced === "True") {
    return "forced";
  } else if (item.hi === "True") {
    return "hi";
  } else if (item.hi === "Excluded") {
    return "nonHi";
  } else {
    return "normal";
  }
};

const subtitleTypePatch = (value: string): Partial<Item> => ({
  hi: value === "hi" ? "True" : value === "nonHi" ? "Excluded" : "False",
  forced: value === "forced" ? "True" : "False",
});

const inclusionValue = (item: Item) => {
  if (item.audioExclude === "True") {
    return "audioExclude";
  } else if (item.audioOnlyInclude === "True") {
    return "audioOnlyInclude";
  } else {
    return "always_include";
  }
};

const inclusionPatch = (value: string): Partial<Item> => ({
  audioExclude: value === "audioExclude" ? "True" : "False",
  audioOnlyInclude: value === "audioOnlyInclude" ? "True" : "False",
});

interface GroupEditorProps {
  group: Group;
  index: number;
  count: number;
  languageOptions: ReturnType<typeof useSelectorOptions<Language.Info>>;
  onMove: (index: number, delta: number) => void;
  onRemove: (index: number) => void;
  onOperator: (index: number, operator: string) => void;
  onAddItem: (index: number) => void;
  onUpdateItem: (
    groupIndex: number,
    itemIndex: number,
    patch: Partial<Item>,
  ) => void;
  onRemoveItem: (groupIndex: number, itemIndex: number) => void;
}

const GroupEditor: FunctionComponent<GroupEditorProps> = ({
  group,
  index,
  count,
  languageOptions,
  onMove,
  onRemove,
  onOperator,
  onAddItem,
  onUpdateItem,
  onRemoveItem,
}) => {
  const columns = useMemo<ColumnDef<Item>[]>(
    () => [
      {
        header: "Language",
        accessorKey: "language",
        cell: ({ row: { original: item, index: itemIndex } }) => (
          <Selector
            {...languageOptions}
            className="table-select"
            value={
              languageOptions.options.find(
                (l) => l.value.code2 === item.language,
              )?.value ?? null
            }
            onChange={(value) => {
              if (value) {
                onUpdateItem(index, itemIndex, { language: value.code2 });
              }
            }}
          ></Selector>
        ),
      },
      {
        header: "Subtitles Type",
        accessorKey: "forced",
        cell: ({ row: { original: item, index: itemIndex } }) => (
          <Select
            value={subtitleTypeValue(item)}
            data={subtitlesTypeOptions}
            onChange={(value) => {
              if (value) {
                onUpdateItem(index, itemIndex, subtitleTypePatch(value));
              }
            }}
          ></Select>
        ),
      },
      {
        header: "Search only when...",
        accessorKey: "audioExclude",
        cell: ({ row: { original: item, index: itemIndex } }) => (
          <Select
            value={inclusionValue(item)}
            data={inclusionOptions}
            onChange={(value) => {
              if (value) {
                onUpdateItem(index, itemIndex, inclusionPatch(value));
              }
            }}
          ></Select>
        ),
      },
      {
        id: "action",
        cell: ({ row }) => (
          <Action
            label="Remove"
            icon={faTrash}
            c="danger"
            onClick={() => onRemoveItem(index, row.index)}
          ></Action>
        ),
      },
    ],
    [index, languageOptions, onRemoveItem, onUpdateItem],
  );

  return (
    <Card withBorder>
      <Stack>
        <Group justify="space-between" wrap="nowrap">
          <Text fw={700}>{`Group ${index + 1}`}</Text>
          <Group gap="xs" wrap="nowrap">
            <Select
              aria-label={`Group ${index + 1} operator`}
              data={operatorOptions}
              value={group.operator}
              w={110}
              onChange={(value) => {
                if (value) {
                  onOperator(index, value);
                }
              }}
            ></Select>
            <Action
              label="Move Up"
              icon={faArrowUp}
              disabled={index === 0}
              onClick={() => onMove(index, -1)}
            ></Action>
            <Action
              label="Move Down"
              icon={faArrowDown}
              disabled={index === count - 1}
              onClick={() => onMove(index, 1)}
            ></Action>
            <Action
              label="Remove Group"
              icon={faTrash}
              c="danger"
              onClick={() => onRemove(index)}
            ></Action>
          </Group>
        </Group>
        <SimpleTable columns={columns} data={group.items}></SimpleTable>
        <Button fullWidth onClick={() => onAddItem(index)}>
          Add Language
        </Button>
        {group.items.length === 0 && (
          <Text c="var(--mantine-color-error)">
            Add at least one language to this group
          </Text>
        )}
      </Stack>
    </Card>
  );
};

interface Props {
  onComplete?: (profile: Language.Profile) => void;
  languages: readonly Language.Info[];
  profile: Language.Profile;
}

const EnhancedProfileEditForm: FunctionComponent<Props> = ({
  onComplete,
  languages,
  profile,
}) => {
  const modals = useModals();

  const form = useForm({
    initialValues: { ...profile, groups: profile.groups ?? [] },
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
      groups: FormUtils.validation(
        (value: Group[]) =>
          value.length > 0 &&
          value.every(
            (group) =>
              group.id !== anyCutoff &&
              group.items.length > 0 &&
              !hasRepeatedLanguage(group.items),
          ),
        "Add at least one group. Each group needs at least one language, and a language cannot repeat with the same subtitle type in a group",
      ),
    },
  });

  const languageOptions = useSelectorOptions(languages, (l) => l.name);

  const mustContainOptions = useSelectorOptions(
    form.values.mustContain,
    (v) => v,
  );

  const mustNotContainOptions = useSelectorOptions(
    form.values.mustNotContain,
    (v) => v,
  );

  const updateGroups = useCallback(
    (update: (groups: Group[]) => Group[]) => {
      form.setValues((values) => ({
        ...values,
        groups: update(values.groups ?? []),
      }));
    },
    [form],
  );

  const addGroup = () => {
    if (languages.length === 0) {
      return;
    }

    const groups = form.values.groups;
    const group: Group = {
      id: nextId(groups.map((g) => g.id)),
      operator: "AND",
      items: [
        newItem(
          nextId(groups.flatMap((g) => g.items).map((item) => item.id)),
          languages[0].code2,
        ),
      ],
    };
    updateGroups((list) => [...list, group]);
  };

  const removeGroup = (index: number) => {
    const removed = form.values.groups[index];
    updateGroups((list) => list.filter((_, i) => i !== index));

    if (removed && form.values.cutoff === removed.id) {
      form.setFieldValue("cutoff", null);
    }
  };

  const moveGroup = (index: number, delta: number) => {
    updateGroups((list) => {
      const target = index + delta;
      if (target < 0 || target >= list.length) {
        return list;
      }

      const reordered = [...list];
      [reordered[index], reordered[target]] = [
        reordered[target],
        reordered[index],
      ];
      return reordered;
    });
  };

  const setOperator = (index: number, operator: string) => {
    updateGroups((list) =>
      list.map((group, i) =>
        i === index
          ? { ...group, operator: operator as Group["operator"] }
          : group,
      ),
    );
  };

  const addItem = (index: number) => {
    if (languages.length === 0) {
      return;
    }

    const groups = form.values.groups;
    const item = newItem(
      nextId(groups.flatMap((g) => g.items).map((i) => i.id)),
      languages[0].code2,
    );
    updateGroups((list) =>
      list.map((group, i) =>
        i === index ? { ...group, items: [...group.items, item] } : group,
      ),
    );
  };

  const updateItem = (
    groupIndex: number,
    itemIndex: number,
    patch: Partial<Item>,
  ) => {
    updateGroups((list) =>
      list.map((group, i) =>
        i === groupIndex
          ? {
              ...group,
              items: group.items.map((item, j) =>
                j === itemIndex ? { ...item, ...patch } : item,
              ),
            }
          : group,
      ),
    );
  };

  const removeItem = (groupIndex: number, itemIndex: number) => {
    updateGroups((list) =>
      list.map((group, i) =>
        i === groupIndex
          ? { ...group, items: group.items.filter((_, j) => j !== itemIndex) }
          : group,
      ),
    );
  };

  const cutoffOptions = useMemo<SelectorOption<{ id: number }>[]>(
    () => [
      ...form.values.groups.map((group, index) => ({
        label: `Group ${index + 1}: ${groupExpression(group)}`,
        value: { id: group.id },
      })),
      { label: "Any group", value: { id: anyCutoff } },
    ],
    [form.values.groups],
  );

  const selectedCutoff = useMemo(
    () =>
      cutoffOptions.find((option) => option.value.id === form.values.cutoff)
        ?.value ?? null,
    [cutoffOptions, form.values.cutoff],
  );

  return (
    <form
      onSubmit={form.onSubmit((value) => {
        LOG("info", "Submitting enhanced language profile", value);
        onComplete?.({
          ...value,
          profileType: "enhanced",
          items: value.groups.flatMap((group) => group.items),
          groups: value.groups,
        });
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
          defaultValue={["Groups"]}
          className={styles.content}
        >
          <Accordion.Item value="Groups">
            <Stack>
              {form.values.groups.map((group, index) => (
                <GroupEditor
                  key={group.id}
                  group={group}
                  index={index}
                  count={form.values.groups.length}
                  languageOptions={languageOptions}
                  onMove={moveGroup}
                  onRemove={removeGroup}
                  onOperator={setOperator}
                  onAddItem={addItem}
                  onUpdateItem={updateItem}
                  onRemoveItem={removeItem}
                ></GroupEditor>
              ))}
              <Button
                fullWidth
                disabled={languages.length === 0}
                onClick={addGroup}
              >
                Add Group
              </Button>
              <Text c="var(--mantine-color-error)">{form.errors.groups}</Text>
              <Selector
                clearable
                label="Cutoff"
                options={cutoffOptions}
                getkey={(value) => String(value.id)}
                value={selectedCutoff}
                onChange={(value) => {
                  form.setFieldValue("cutoff", value?.id ?? null);
                }}
              ></Selector>
              <Text size="sm">
                Once the cutoff group is satisfied, languages from lower groups
                are not searched. Any group means any satisfied group meets the
                cutoff.
              </Text>
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
        <Button type="submit">Confirm</Button>
      </Stack>
    </form>
  );
};

export const EnhancedProfileEditModal = withModal(
  EnhancedProfileEditForm,
  "enhanced-languages-profile-editor",
  {
    title: "Edit Enhanced Languages Profile",
    size: "xl",
  },
);
