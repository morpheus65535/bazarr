import {
  ActionButton,
  BaseModal,
  BaseModalProps,
  Chips,
  LanguageSelector,
  Selector,
  SelectorOption,
  SimpleTable,
} from "@/components";
import { useModalControl, usePayload } from "@/modules/redux/hooks/modal";
import { BuildKey } from "@/utilities";
import { LOG } from "@/utilities/console";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import {
  createContext,
  FunctionComponent,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Button, Form } from "react-bootstrap";
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

const LanguagesProfileModal: FunctionComponent<Props & BaseModalProps> = (
  props
) => {
  const { update, ...modal } = props;

  const profile = usePayload<Language.Profile>(modal.modalKey);

  const { hide } = useModalControl();

  const languages = useLatestEnabledLanguages();

  const [current, setProfile] = useState(createDefaultProfile);

  useEffect(() => {
    if (profile) {
      setProfile(profile);
    } else {
      setProfile(createDefaultProfile);
    }
  }, [profile]);

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
            () => languages.find((l) => l.code2 === code) ?? null,
            [code]
          );
          const mutate = useRowMutation();
          return (
            <div style={{ width: "8rem" }}>
              <LanguageSelector
                options={languages}
                value={lang}
                onChange={(l) => {
                  if (l) {
                    item.language = l.code2;
                    mutate(row.index, item);
                  }
                }}
              ></LanguageSelector>
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
            <Form.Check
              custom
              id={BuildKey(item.id, item.language, "forced")}
              checked={value === "True"}
              onChange={(v) => {
                item.forced = v.target.checked ? "True" : "False";
                mutate(row.index, item);
              }}
            ></Form.Check>
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
            <Form.Check
              custom
              id={BuildKey(item.id, item.language, "hi")}
              checked={value === "True"}
              onChange={(v) => {
                item.hi = v.target.checked ? "True" : "False";
                mutate(row.index, item);
              }}
            ></Form.Check>
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
            <Form.Check
              custom
              id={BuildKey(item.id, item.language, "audio")}
              checked={value === "True"}
              onChange={(v) => {
                item.audio_exclude = v.target.checked ? "True" : "False";
                mutate(row.index, item);
              }}
            ></Form.Check>
          );
        },
      },
      {
        id: "action",
        accessor: "id",
        Cell: ({ row }) => {
          const mutate = useRowMutation();
          return (
            <ActionButton
              icon={faTrash}
              onClick={() => mutate(row.index)}
            ></ActionButton>
          );
        },
      },
    ],
    [languages]
  );

  return (
    <BaseModal size="lg" title="Languages Profile" footer={footer} {...modal}>
      <Input>
        <Form.Control
          type="text"
          placeholder="Name"
          value={current.name}
          onChange={(v) => {
            updateProfile("name", v.target.value);
          }}
        ></Form.Control>
      </Input>
      <Input>
        <RowContext.Provider value={mutateRow}>
          <SimpleTable
            responsive={false}
            columns={columns}
            data={current.items}
          ></SimpleTable>
        </RowContext.Provider>
        <Button block variant="light" onClick={addItem}>
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
        <Chips
          value={current.mustContain}
          onChange={(mc) => updateProfile("mustContain", mc)}
        ></Chips>
        <Message>
          Subtitles release info must include one of those words or they will be
          excluded from search results (regex supported).
        </Message>
      </Input>
      <Input name="Release info must not contain">
        <Chips
          value={current.mustNotContain}
          onChange={(mnc: string[]) => {
            updateProfile("mustNotContain", mnc);
          }}
        ></Chips>
        <Message>
          Subtitles release info including one of those words (case insensitive)
          will be excluded from search results (regex supported).
        </Message>
      </Input>
      <Input name="Original Format">
        <Selector
          options={[
            { label: "Enable", value: true },
            { label: "Disable", value: false },
          ]}
          value={current.originalFormat || false}
          onChange={(value) => updateProfile("originalFormat", value)}
        ></Selector>
        <Message>Download subtitle file without format conversion</Message>
      </Input>
    </BaseModal>
  );
};

export default LanguagesProfileModal;
