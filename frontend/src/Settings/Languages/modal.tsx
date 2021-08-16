import { faTrash } from "@fortawesome/free-solid-svg-icons";
import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Button, Form } from "react-bootstrap";
import { Column, TableUpdater } from "react-table";
import { useEnabledLanguagesContext } from ".";
import {
  ActionButton,
  BaseModal,
  BaseModalProps,
  LanguageSelector,
  Selector,
  SimpleTable,
  useModalInformation,
} from "../../components";
import { BuildKey } from "../../utilites";
import { Input, Message } from "../components";
import { cutoffOptions } from "./options";
interface Props {
  update: (profile: Language.Profile) => void;
}

function createDefaultProfile(): Language.Profile {
  return {
    profileId: -1,
    name: "",
    items: [],
    cutoff: null,
  };
}

const LanguagesProfileModal: FunctionComponent<Props & BaseModalProps> = (
  props
) => {
  const { update, ...modal } = props;

  const { payload: profile, closeModal } =
    useModalInformation<Language.Profile>(modal.modalKey);

  const languages = useEnabledLanguagesContext();

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

  const updateRow = useCallback<TableUpdater<Language.ProfileItem>>(
    (row, item: Language.ProfileItem) => {
      const list = [...current.items];
      if (item) {
        list[row.index] = item;
      } else {
        list.splice(row.index, 1);
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
        closeModal();
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
        Cell: ({ value, row, externalUpdate }) => {
          const code = value;
          const item = row.original;
          const lang = useMemo(
            () => languages.find((l) => l.code2 === code) ?? null,
            [code]
          );
          return (
            <div style={{ width: "8rem" }}>
              <LanguageSelector
                options={languages}
                value={lang}
                onChange={(l) => {
                  if (l) {
                    item.language = l.code2;
                    externalUpdate && externalUpdate(row, item);
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
        Cell: ({ row, value, externalUpdate }) => {
          const item = row.original;
          return (
            <Form.Check
              custom
              id={BuildKey(item.id, item.language, "forced")}
              checked={value === "True"}
              onChange={(v) => {
                item.forced = v.target.checked ? "True" : "False";
                externalUpdate && externalUpdate(row, item);
              }}
            ></Form.Check>
          );
        },
      },
      {
        Header: "HI",
        accessor: "hi",
        Cell: ({ row, value, externalUpdate }) => {
          const item = row.original;
          return (
            <Form.Check
              custom
              id={BuildKey(item.id, item.language, "hi")}
              checked={value === "True"}
              onChange={(v) => {
                item.hi = v.target.checked ? "True" : "False";
                externalUpdate && externalUpdate(row, item);
              }}
            ></Form.Check>
          );
        },
      },
      {
        Header: "Exclude Audio",
        accessor: "audio_exclude",
        Cell: ({ row, value, externalUpdate }) => {
          const item = row.original;
          return (
            <Form.Check
              custom
              id={BuildKey(item.id, item.language, "audio")}
              checked={value === "True"}
              onChange={(v) => {
                item.audio_exclude = v.target.checked ? "True" : "False";
                externalUpdate && externalUpdate(row, item);
              }}
            ></Form.Check>
          );
        },
      },
      {
        id: "action",
        accessor: "id",
        Cell: ({ row, externalUpdate }) => {
          return (
            <ActionButton
              icon={faTrash}
              onClick={() => externalUpdate && externalUpdate(row)}
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
        <SimpleTable
          responsive={false}
          columns={columns}
          data={current.items}
          externalUpdate={updateRow}
        ></SimpleTable>
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
    </BaseModal>
  );
};

export default LanguagesProfileModal;
