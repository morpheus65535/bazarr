import React, {
  FunctionComponent,
  useMemo,
  useState,
  useCallback,
  useEffect,
} from "react";
import { Button, Form } from "react-bootstrap";
import { Column } from "react-table";
import {
  ActionIcon,
  BasicTable,
  BasicModal,
  BasicModalProps,
  LanguageSelector,
  useCloseModal,
  usePayload,
  Selector,
} from "../../components";
import { Input, Message } from "../components";
import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { useEnabledLanguages } from ".";
import { cutoffOptions } from "./options";
interface Props {
  update: (profile: LanguagesProfile) => void;
}

const LanguagesProfileModal: FunctionComponent<Props & BasicModalProps> = (
  props
) => {
  const { update, ...modal } = props;

  const profile = usePayload<LanguagesProfile>();

  const closeModal = useCloseModal();

  const languages = useEnabledLanguages();

  const [current, setProfile] = useState(
    profile ?? {
      profileId: -1,
      name: "",
      items: [],
      cutoff: null,
    }
  );

  useEffect(() => {
    if (profile) {
      setProfile(profile);
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
    <K extends keyof LanguagesProfile>(key: K, value: LanguagesProfile[K]) => {
      const object = { ...current };
      object[key] = value;
      setProfile(object);
    },
    [current]
  );

  const updateItem = useCallback(
    (item: LanguagesProfileItem) => {
      const list = [...current.items];
      const idx = list.findIndex((v) => v.id === item.id);

      if (idx !== -1) {
        list[idx] = item;
        updateProfile("items", list);
      }
    },
    [current.items, updateProfile]
  );

  const addItem = useCallback(() => {
    const id =
      1 +
      current.items.reduce<number>((val, item) => Math.max(item.id, val), 0);

    if (languages.length > 0) {
      const language = languages[0].code2;

      const item: LanguagesProfileItem = {
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

  const removeItem = useCallback(
    (id: number) => {
      const list = [...current.items];
      const idx = list.findIndex((v) => v.id === id);

      if (idx !== -1) {
        list.splice(idx, 1);
      }

      updateProfile("items", list);
    },
    [current.items, updateProfile]
  );

  const footer = useMemo(
    () => (
      <Button
        onClick={() => {
          closeModal();
          update(current);
        }}
      >
        Save
      </Button>
    ),
    [update, current, closeModal]
  );

  const columns = useMemo<Column<LanguagesProfileItem>[]>(
    () => [
      {
        Header: "ID",
        accessor: "id",
      },
      {
        Header: "Language",
        accessor: "language",
        Cell: (row) => {
          const code = row.value;
          const item = row.row.original;
          const lang = useMemo(() => languages.find((l) => l.code2 === code), [
            code,
          ]);
          return (
            <div style={{ width: "8rem" }}>
              <LanguageSelector
                options={languages}
                defaultValue={lang}
                onChange={(l) => {
                  if (l) {
                    item.language = l.code2;
                    updateItem(item);
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
        Cell: (row) => {
          const item = row.row.original;
          return (
            <Form.Check
              defaultChecked={row.value === "True"}
              onChange={(v) => {
                item.forced = v.target.checked ? "True" : "False";
                updateItem(item);
              }}
            ></Form.Check>
          );
        },
      },
      {
        Header: "HI",
        accessor: "hi",
        Cell: (row) => {
          const item = row.row.original;
          return (
            <Form.Check
              defaultChecked={row.value === "True"}
              onChange={(v) => {
                item.hi = v.target.checked ? "True" : "False";
                updateItem(item);
              }}
            ></Form.Check>
          );
        },
      },
      {
        Header: "Exclude Audio",
        accessor: "audio_exclude",
        Cell: (row) => {
          const item = row.row.original;
          return (
            <Form.Check
              defaultChecked={row.value === "True"}
              onChange={(v) => {
                item.audio_exclude = v.target.checked ? "True" : "False";
                updateItem(item);
              }}
            ></Form.Check>
          );
        },
      },
      {
        id: "action",
        accessor: "id",
        Cell: (row) => {
          return (
            <ActionIcon
              icon={faTrash}
              onClick={() => removeItem(row.value)}
            ></ActionIcon>
          );
        },
      },
    ],
    [languages, removeItem, updateItem]
  );

  return (
    <BasicModal size="lg" title="Languages Profile" footer={footer} {...modal}>
      <Input>
        <Form.Control
          type="text"
          placeholder="Name"
          defaultValue={profile?.name}
          onChange={(v) => {
            updateProfile("name", v.target.value);
          }}
        ></Form.Control>
      </Input>
      <Input>
        <BasicTable
          showPageControl={false}
          responsive={false}
          columns={columns}
          data={current?.items ?? []}
        ></BasicTable>
        <Button block variant="light" onClick={addItem}>
          Add
        </Button>
      </Input>
      <Input name="Cutoff">
        <Selector
          options={cutoff}
          defaultValue={profile?.cutoff}
          onChange={(num) => {
            if (num === undefined) {
              num = null;
            }
            updateProfile("cutoff", num);
          }}
        ></Selector>
        <Message type="info">Ignore others if existing</Message>
      </Input>
    </BasicModal>
  );
};

export default LanguagesProfileModal;
