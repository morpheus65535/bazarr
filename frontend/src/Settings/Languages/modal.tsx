import React, {
  FunctionComponent,
  useMemo,
  useState,
  useCallback,
} from "react";
import { Button } from "react-bootstrap";
import { Column } from "react-table";
import {
  ActionIcon,
  BasicTable,
  BasicModal,
  BasicModalProps,
  Selector,
  LanguageSelector,
} from "../../components";
import { Input, Text, Message, Check } from "../components";

import { faTrash } from "@fortawesome/free-solid-svg-icons";

interface Props {
  languages: Language[];
  profile: LanguagesProfile;
  update: (profile: LanguagesProfile) => void;
}

const cutoffOptions: LooseObject = {
  disabled: "Disabled",
  "65535": "Any",
};

const LanguagesProfileModal: FunctionComponent<Props & BasicModalProps> = (
  props
) => {
  const { profile, update, languages, ...modal } = props;

  const [current, setProfile] = useState(profile);

  const cutoff = useMemo(() => {
    const options = { ...cutoffOptions };
    current.items.forEach((v) => {
      options[v.id] = `ID ${v.id}`;
    });
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
    (item: LangaugesProfileItem) => {
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

      const item: LangaugesProfileItem = {
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
          modal.onClose();
          update(current);
        }}
      >
        Save
      </Button>
    ),
    [update, modal, current]
  );

  const columns = useMemo<Column<LangaugesProfileItem>[]>(
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
            <LanguageSelector
              variant="light"
              options={languages}
              defaultSelect={lang}
              onChange={(l: Language) => {
                item.language = l.code2;
                updateItem(item);
              }}
            ></LanguageSelector>
          );
        },
      },
      {
        Header: "Forced",
        accessor: "forced",
        Cell: (row) => {
          const item = row.row.original;
          return (
            <Check
              defaultValue={row.value === "True"}
              onChange={(v) => {
                item.forced = v ? "True" : "False";
                updateItem(item);
              }}
            ></Check>
          );
        },
      },
      {
        Header: "HI",
        accessor: "hi",
        Cell: (row) => {
          const item = row.row.original;
          return (
            <Check
              defaultValue={row.value === "True"}
              onChange={(v) => {
                item.hi = v ? "True" : "False";
                updateItem(item);
              }}
            ></Check>
          );
        },
      },
      {
        Header: "Exclude Audio",
        accessor: "audio_exclude",
        Cell: (row) => {
          const item = row.row.original;
          return (
            <Check
              defaultValue={row.value === "True"}
              onChange={(v) => {
                item.audio_exclude = v ? "True" : "False";
                updateItem(item);
              }}
            ></Check>
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
      <Input name="Name">
        <Text
          defaultValue={current?.name}
          onChange={(v) => {
            updateProfile("name", v.toString());
          }}
        ></Text>
      </Input>
      <Input>
        <BasicTable
          pageControl={false}
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
          nullKey="disabled"
          options={cutoff}
          defaultKey={
            current.cutoff !== null ? current.cutoff.toString() : undefined
          }
          onSelect={(k) => {
            let num: number | null = parseInt(k);
            if (isNaN(num)) {
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
