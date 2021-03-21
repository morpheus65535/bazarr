import { faQuestionCircle } from "@fortawesome/free-regular-svg-icons";
import {
  faCheck,
  faCircleNotch,
  faClock,
  faCode,
  faDeaf,
  faExchangeAlt,
  faFilm,
  faImage,
  faLanguage,
  faMagic,
  faMinus,
  faPaintBrush,
  faPlay,
  faPlus,
  faTextHeight,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import {
  Badge,
  Button,
  ButtonGroup,
  Dropdown,
  Form,
  InputGroup,
} from "react-bootstrap";
import { Column, useRowSelect } from "react-table";
import {
  ActionButton,
  ActionButtonItem,
  LanguageSelector,
  LanguageText,
  Selector,
  SimpleTable,
  usePayload,
  useShowModal,
} from "..";
import { useLanguages } from "../../@redux/hooks";
import { SubtitlesApi } from "../../apis";
import { isMovie, submodProcessColor } from "../../utilites";
import { log } from "../../utilites/logger";
import { useCustomSelection } from "../tables/plugins";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useCloseModalUntil } from "./provider";
import { avaliableTranslation, colorOptions } from "./toolOptions";

type SupportType = Item.Episode | Item.Movie;

type TableColumnType = FormType.ModifySubtitle & {
  _language: Language;
};

enum State {
  Pending,
  Processing,
  Done,
}

type ProcessState = StrictObject<State>;

// TODO: Extract this
interface StateIconProps {
  state: State;
}

const StateIcon: FunctionComponent<StateIconProps> = ({ state }) => {
  let icon = faQuestionCircle;
  switch (state) {
    case State.Pending:
    case State.Processing:
      icon = faCircleNotch;
      break;
    case State.Done:
      icon = faCheck;
      break;
  }
  return (
    <FontAwesomeIcon
      icon={icon}
      spin={state === State.Processing}
    ></FontAwesomeIcon>
  );
};

function getIdAndType(item: SupportType): [number, "episode" | "movie"] {
  if (isMovie(item)) {
    return [item.radarrId, "movie"];
  } else {
    return [item.sonarrEpisodeId, "episode"];
  }
}

function submodProcessFrameRate(from: number, to: number) {
  return `change_FPS(from=${from},to=${to})`;
}

function submodProcessOffset(h: number, m: number, s: number, ms: number) {
  return `shift_offset(h=${h},m=${m},s=${s},ms=${ms})`;
}

interface ToolModalProps {
  process: (
    action: string,
    override?: Partial<FormType.ModifySubtitle>
  ) => void;
}

const AddColorModal: FunctionComponent<BaseModalProps & ToolModalProps> = (
  props
) => {
  const { process, ...modal } = props;
  const [selection, setSelection] = useState<Nullable<string>>(null);

  const submit = useCallback(() => {
    if (selection) {
      const action = submodProcessColor(selection);
      process(action);
    }
  }, [selection, process]);

  const footer = useMemo(
    () => (
      <Button disabled={selection === null} onClick={submit}>
        Save
      </Button>
    ),
    [selection, submit]
  );
  return (
    <BaseModal title="Choose Color" footer={footer} {...modal}>
      <Selector options={colorOptions} onChange={setSelection}></Selector>
    </BaseModal>
  );
};

const FrameRateModal: FunctionComponent<BaseModalProps & ToolModalProps> = (
  props
) => {
  const { process, ...modal } = props;

  const [from, setFrom] = useState<Nullable<number>>(null);
  const [to, setTo] = useState<Nullable<number>>(null);

  const canSave = from !== null && to !== null && from !== to;

  const submit = useCallback(() => {
    if (canSave) {
      const action = submodProcessFrameRate(from!, to!);
      process(action);
    }
  }, [canSave, from, to, process]);

  const footer = useMemo(
    () => (
      <Button disabled={!canSave} onClick={submit}>
        Save
      </Button>
    ),
    [submit, canSave]
  );

  return (
    <BaseModal title="Change Frame Rate" footer={footer} {...modal}>
      <InputGroup className="px-2">
        <Form.Control
          placeholder="From"
          type="number"
          onChange={(e) => {
            const value = parseFloat(e.currentTarget.value);
            if (isNaN(value)) {
              setFrom(null);
            } else {
              setFrom(value);
            }
          }}
        ></Form.Control>
        <Form.Control
          placeholder="To"
          type="number"
          onChange={(e) => {
            const value = parseFloat(e.currentTarget.value);
            if (isNaN(value)) {
              setTo(null);
            } else {
              setTo(value);
            }
          }}
        ></Form.Control>
      </InputGroup>
    </BaseModal>
  );
};

const AdjustTimesModal: FunctionComponent<BaseModalProps & ToolModalProps> = (
  props
) => {
  const { process, ...modal } = props;

  const [isPlus, setPlus] = useState(true);
  const [offset, setOffset] = useState<[number, number, number, number]>([
    0,
    0,
    0,
    0,
  ]);

  const updateOffset = useCallback(
    (idx: number) => {
      return (e: any) => {
        let value = parseFloat(e.currentTarget.value);
        if (isNaN(value)) {
          value = 0;
        }
        const newOffset = [...offset] as [number, number, number, number];
        newOffset[idx] = value;
        setOffset(newOffset);
      };
    },
    [offset]
  );

  const canSave = offset.some((v) => v !== 0);

  const submit = useCallback(() => {
    if (canSave) {
      const newOffset = offset.map((v) => (isPlus ? v : -v));
      const action = submodProcessOffset(
        newOffset[0],
        newOffset[1],
        newOffset[2],
        newOffset[3]
      );
      process(action);
    }
  }, [process, canSave, offset, isPlus]);

  const footer = useMemo(
    () => (
      <Button disabled={!canSave} onClick={submit}>
        Save
      </Button>
    ),
    [submit, canSave]
  );

  return (
    <BaseModal title="Adjust Times" footer={footer} {...modal}>
      <InputGroup>
        <InputGroup.Prepend>
          <Button
            variant="secondary"
            title={isPlus ? "Later" : "Earlier"}
            onClick={() => setPlus(!isPlus)}
          >
            <FontAwesomeIcon icon={isPlus ? faPlus : faMinus}></FontAwesomeIcon>
          </Button>
        </InputGroup.Prepend>
        <Form.Control
          type="number"
          placeholder="hour"
          onChange={updateOffset(0)}
        ></Form.Control>
        <Form.Control
          type="number"
          placeholder="min"
          onChange={updateOffset(1)}
        ></Form.Control>
        <Form.Control
          type="number"
          placeholder="sec"
          onChange={updateOffset(2)}
        ></Form.Control>
        <Form.Control
          type="number"
          placeholder="ms"
          onChange={updateOffset(3)}
        ></Form.Control>
      </InputGroup>
    </BaseModal>
  );
};

const TranslateModal: FunctionComponent<BaseModalProps & ToolModalProps> = ({
  process,
  ...modal
}) => {
  const [languages] = useLanguages(true);

  const avaliable = useMemo(
    () => languages.filter((v) => v.code2 in avaliableTranslation),
    [languages]
  );

  const [selectedLanguage, setLanguage] = useState<Nullable<Language>>(null);

  const submit = useCallback(() => {
    if (selectedLanguage) {
      process("translate", { language: selectedLanguage.code2 });
    }
  }, [selectedLanguage, process]);

  const footer = useMemo(
    () => (
      <Button disabled={!selectedLanguage} onClick={submit}>
        Translate
      </Button>
    ),
    [submit, selectedLanguage]
  );

  return (
    <BaseModal title="Translate to" footer={footer} {...modal}>
      <LanguageSelector
        options={avaliable}
        onChange={setLanguage}
      ></LanguageSelector>
    </BaseModal>
  );
};

const STM: FunctionComponent<BaseModalProps> = (props) => {
  const items = usePayload<SupportType[]>(props.modalKey);

  const [updating, setUpdate] = useState<boolean>(false);
  const [processState, setProcessState] = useState<ProcessState>({});
  const [selections, setSelections] = useState<TableColumnType[]>([]);

  const closeUntil = useCloseModalUntil(props.modalKey);

  const process = useCallback(
    async (action: string, override?: Partial<FormType.ModifySubtitle>) => {
      log("info", "executing action", action);
      closeUntil();
      setUpdate(true);

      let states = selections.reduce<ProcessState>(
        (v, curr) => ({ [curr.path]: State.Pending, ...v }),
        {}
      );
      setProcessState(states);

      for (const raw of selections) {
        states = {
          ...states,
          [raw.path]: State.Processing,
        };
        setProcessState(states);
        const form: FormType.ModifySubtitle = {
          id: raw.id,
          type: raw.type,
          language: raw.language,
          path: raw.path,
          ...override,
        };
        await SubtitlesApi.modify(action, form);

        states = {
          ...states,
          [raw.path]: State.Done,
        };
        setProcessState(states);
      }
      setUpdate(false);
    },
    [closeUntil, selections]
  );

  const showModal = useShowModal();

  const columns: Column<TableColumnType>[] = useMemo<Column<TableColumnType>[]>(
    () => [
      {
        id: "state",
        accessor: "path",
        selectHide: true,
        Cell: ({ value, loose }) => {
          if (loose) {
            const stateList = loose[0] as ProcessState;
            if (value in stateList) {
              const state = stateList[value];
              return <StateIcon state={state}></StateIcon>;
            }
          }
          return null;
        },
      },
      {
        Header: "Language",
        accessor: "_language",
        Cell: ({ value }) => (
          <Badge variant="secondary">
            <LanguageText text={value} long={true}></LanguageText>
          </Badge>
        ),
      },
      {
        id: "file",
        Header: "File",
        accessor: "path",
        Cell: (row) => {
          const path = row.value!;

          let idx = path.lastIndexOf("/");

          if (idx === -1) {
            idx = path.lastIndexOf("\\");
          }

          if (idx !== -1) {
            return path.slice(idx + 1);
          } else {
            return path;
          }
        },
      },
    ],
    []
  );

  const data = useMemo<TableColumnType[]>(
    () =>
      items?.flatMap((item) => {
        const [id, type] = getIdAndType(item);
        return item.subtitles.flatMap((v) => {
          if (v.path !== null) {
            return [
              {
                id,
                type,
                language: v.code2,
                path: v.path,
                _language: v,
              },
            ];
          } else {
            return [];
          }
        });
      }) ?? [],
    [items]
  );

  const plugins = [useRowSelect, useCustomSelection];

  const footer = useMemo(
    () => (
      <Dropdown as={ButtonGroup} onSelect={(k) => k && process(k)}>
        <ActionButton
          size="sm"
          loading={updating}
          disabled={selections.length === 0}
          icon={faPlay}
          onClick={() => process("sync")}
        >
          Sync
        </ActionButton>
        <Dropdown.Toggle
          disabled={updating || selections.length === 0}
          split
          variant="light"
          size="sm"
          className="px-2"
        ></Dropdown.Toggle>
        <Dropdown.Menu>
          <Dropdown.Item eventKey="remove_HI">
            <ActionButtonItem icon={faDeaf}>Remove HI Tags</ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item eventKey="remove_tags">
            <ActionButtonItem icon={faCode}>Remove Style Tags</ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item eventKey="OCR_fixes">
            <ActionButtonItem icon={faImage}>OCR Fixes</ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item eventKey="common">
            <ActionButtonItem icon={faMagic}>Common Fixes</ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item eventKey="fix_uppercase">
            <ActionButtonItem icon={faTextHeight}>
              Fix Uppercase
            </ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item eventKey="reverse_rtl">
            <ActionButtonItem icon={faExchangeAlt}>
              Reverse RTL
            </ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item onSelect={() => showModal("add-color")}>
            <ActionButtonItem icon={faPaintBrush}>Add Color</ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item onSelect={() => showModal("change-frame-rate")}>
            <ActionButtonItem icon={faFilm}>Change Frame Rate</ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item onSelect={() => showModal("adjust-times")}>
            <ActionButtonItem icon={faClock}>Adjust Times</ActionButtonItem>
          </Dropdown.Item>
          <Dropdown.Item onSelect={() => showModal("translate-sub")}>
            <ActionButtonItem icon={faLanguage}>Translate</ActionButtonItem>
          </Dropdown.Item>
        </Dropdown.Menu>
      </Dropdown>
    ),
    [showModal, updating, selections.length, process]
  );

  return (
    <React.Fragment>
      <BaseModal
        title={"Subtitle Tools"}
        footer={footer}
        closeable={!updating}
        {...props}
      >
        <SimpleTable
          isSelecting={!updating && data.length !== 0}
          emptyText="No External Subtitles Found"
          plugins={plugins}
          columns={columns}
          onSelect={setSelections}
          data={data}
          loose={[processState]}
        ></SimpleTable>
      </BaseModal>
      <AddColorModal process={process} modalKey="add-color"></AddColorModal>
      <FrameRateModal
        process={process}
        modalKey="change-frame-rate"
      ></FrameRateModal>
      <AdjustTimesModal
        process={process}
        modalKey="adjust-times"
      ></AdjustTimesModal>
      <TranslateModal
        process={process}
        modalKey="translate-sub"
      ></TranslateModal>
    </React.Fragment>
  );
};

export default STM;
