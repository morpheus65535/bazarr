import {
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
  useModalPayload,
  useShowModal,
} from "..";
import { dispatchTask } from "../../@modules/task";
import { createTask } from "../../@modules/task/utilities";
import { useEnabledLanguages } from "../../@redux/hooks";
import { SubtitlesApi } from "../../apis";
import { isMovie, submodProcessColor } from "../../utilities";
import { log } from "../../utilities/logger";
import { useCustomSelection } from "../tables/plugins";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useCloseModal } from "./hooks";
import { availableTranslation, colorOptions } from "./toolOptions";

type SupportType = Item.Episode | Item.Movie;

type TableColumnType = FormType.ModifySubtitle & {
  _language: Language.Info;
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
    0, 0, 0, 0,
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
  const languages = useEnabledLanguages();

  const available = useMemo(
    () => languages.filter((v) => v.code2 in availableTranslation),
    [languages]
  );

  const [selectedLanguage, setLanguage] =
    useState<Nullable<Language.Info>>(null);

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
      <Form.Label>
        Enabled languages not listed here are unsupported by Google Translate.
      </Form.Label>
      <LanguageSelector
        options={available}
        onChange={setLanguage}
      ></LanguageSelector>
    </BaseModal>
  );
};

const TaskGroupName = "Modifying Subtitles";

const CanSelectSubtitle = (item: TableColumnType) => {
  return item.path.endsWith(".srt");
};

const STM: FunctionComponent<BaseModalProps> = ({ ...props }) => {
  const payload = useModalPayload<SupportType[]>(props.modalKey);
  const [selections, setSelections] = useState<TableColumnType[]>([]);

  const closeModal = useCloseModal();

  const process = useCallback(
    (action: string, override?: Partial<FormType.ModifySubtitle>) => {
      log("info", "executing action", action);
      closeModal(props.modalKey);

      const tasks = selections.map((s) => {
        const form: FormType.ModifySubtitle = {
          id: s.id,
          type: s.type,
          language: s.language,
          path: s.path,
          ...override,
        };
        return createTask(
          s.path,
          s.id,
          SubtitlesApi.modify.bind(SubtitlesApi),
          action,
          form
        );
      });

      dispatchTask(TaskGroupName, tasks, "Modifying subtitles...");
    },
    [closeModal, selections, props.modalKey]
  );

  const showModal = useShowModal();

  const columns: Column<TableColumnType>[] = useMemo<Column<TableColumnType>[]>(
    () => [
      {
        Header: "Language",
        accessor: "_language",
        Cell: ({ value }) => (
          <Badge variant="secondary">
            <LanguageText text={value} long></LanguageText>
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
      payload?.flatMap((item) => {
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
    [payload]
  );

  const plugins = [useRowSelect, useCustomSelection];

  const footer = useMemo(
    () => (
      <Dropdown as={ButtonGroup} onSelect={(k) => k && process(k)}>
        <ActionButton
          size="sm"
          disabled={selections.length === 0}
          icon={faPlay}
          onClick={() => process("sync")}
        >
          Sync
        </ActionButton>
        <Dropdown.Toggle
          disabled={selections.length === 0}
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
    [showModal, selections.length, process]
  );

  return (
    <React.Fragment>
      <BaseModal title={"Subtitle Tools"} footer={footer} {...props}>
        <SimpleTable
          isSelecting={data.length !== 0}
          emptyText="No External Subtitles Found"
          plugins={plugins}
          columns={columns}
          onSelect={setSelections}
          canSelect={CanSelectSubtitle}
          data={data}
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
