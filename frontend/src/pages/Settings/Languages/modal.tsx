import { Selector, SelectorOption, SimpleTable } from "@/components";
import { Language } from "@/components/bazarr";
import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { useSelectorOptions } from "@/utilities";
import { LOG } from "@/utilities/console";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  ActionIcon,
  Button,
  Checkbox,
  MultiSelect,
  Switch,
  TextInput,
} from "@mantine/core";
import {
  createContext,
  FunctionComponent,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { Column } from "react-table";
import { useLatestEnabledLanguages } from ".";
import { Input, Message } from "../components";
import { cutoffOptions } from "./options";

type ModifyFn = (index: number, item?: Language.ProfileItem) => void;

const RowContext = createContext<ModifyFn>(() => {
  LOG("error", "RowContext not initialized");
});

function useRowMutation() {
  return useContext(RowContext);
}

interface Props {
  update: (profile: Language.Profile) => void;
}

function createDefaultProfile(): Language.Profile {
  return {
    profileId: -1,
    name: "",
    items: [],
    cutoff: null,
    mustContain: [],
    mustNotContain: [],
    originalFormat: false,
  };
}

const LanguagesProfileModal: FunctionComponent<Props> = ({ update }) => {
  const profile = usePayload<Language.Profile>();

  const { hide } = useModalControl();

  const languages = useLatestEnabledLanguages();

  const languageOptions = useSelectorOptions(languages, (l) => l.name);

  const [current, setProfile] = useState(createDefaultProfile);

  const Modal = useModal({
    size: "lg",
    onMounted: () => {
      setProfile(profile ?? createDefaultProfile);
    },
  });

  const cutoff: SelectorOption<number>[] = useMemo(() => {
    const options = [...cutoffOptions];

    const newOptions = current.items.map<SelectorOption<number>>((v) => ({
      label: `ID ${v.id} (${v.language})`,
      value: v.id,
    }));

    options.push(...newOptions);

    return options;
  }, [current.items]);

  const updateProfile = useCallback(
    <K extends keyof Language.Profile>(key: K, value: Language.Profile[K]) => {
      const newProfile = { ...current };
      newProfile[key] = value;
      setProfile(newProfile);
    },
    [current]
  );

  const mutateRow = useCallback(
    (index: number, item?: Language.ProfileItem) => {
      const list = [...current.items];
      if (item) {
        list[index] = item;
      } else {
        list.splice(index, 1);
      }
      updateProfile("items", list);
    },
    [current.items, updateProfile]
  );

  const addItem = useCallback(() => {
    const id =
      1 +
      current.items.reduce<number>((val, item) => Math.max(item.id, val), 0);

    if (languages.length > 0) {
      const language = languages[0].code2;

      const item: Language.ProfileItem = {
        id,
        language,
        audio_exclude: "False",
        hi: "False",
        forced: "False",
      };

      const list = [...current.items];

      list.push(item);
      updateProfile("items", list);
    }
  }, [current.items, updateProfile, languages]);

  const canSave = current.name.length > 0 && current.items.length > 0;

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
            <div style={{ width: "8rem" }}>
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
            </div>
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
            <ActionIcon onClick={() => mutate(row.index)}>
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </ActionIcon>
          );
        },
      },
    ],
    [languageOptions]
  );

  const footer = (
    <Button
      disabled={!canSave}
      onClick={() => {
        hide();
        update(current);
      }}
    >
      Save
    </Button>
  );

  return (
    <Modal title="Languages Profile" footer={footer}>
      <Input>
        <TextInput
          placeholder="Name"
          value={current.name}
          onChange={(v) => {
            updateProfile("name", v.target.value);
          }}
        ></TextInput>
      </Input>
      <Input>
        <RowContext.Provider value={mutateRow}>
          <SimpleTable columns={columns} data={current.items}></SimpleTable>
        </RowContext.Provider>
        <Button fullWidth color="light" onClick={addItem}>
          Add
        </Button>
      </Input>
      <Input name="Cutoff">
        <Selector
          clearable
          options={cutoff}
          value={current.cutoff}
          onChange={(num) => updateProfile("cutoff", num)}
        ></Selector>
        <Message>Ignore others if existing</Message>
      </Input>
      <Input name="Release info must contain">
        <MultiSelect
          creatable
          searchable
          value={current?.mustContain ?? []}
          data={current?.mustContain ?? []}
          onChange={(mc) => updateProfile("mustContain", mc)}
          onCreate={(v) =>
            updateProfile("mustContain", [...(current.mustContain ?? []), v])
          }
        ></MultiSelect>
        <Message>
          Subtitles release info must include one of those words or they will be
          excluded from search results (regex supported).
        </Message>
      </Input>
      <Input name="Release info must not contain">
        <MultiSelect
          creatable
          searchable
          value={current?.mustNotContain ?? []}
          data={current?.mustNotContain ?? []}
          onChange={(mnc: string[]) => {
            updateProfile("mustNotContain", mnc);
          }}
          onCreate={(v) =>
            updateProfile("mustNotContain", [
              ...(current?.mustNotContain ?? []),
              v,
            ])
          }
        ></MultiSelect>
        <Message>
          Subtitles release info including one of those words (case insensitive)
          will be excluded from search results (regex supported).
        </Message>
      </Input>
      <Input>
        <Switch
          label="Use Original Format"
          checked={current.originalFormat ?? false}
          onChange={({ currentTarget: { checked } }) =>
            updateProfile("originalFormat", checked)
          }
        ></Switch>
        <Message>Download subtitle file without format conversion</Message>
      </Input>
    </Modal>
  );
};

export default withModal(LanguagesProfileModal, "languages-profile-editor");
