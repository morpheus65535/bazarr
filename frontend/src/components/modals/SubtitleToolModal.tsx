import { useSubtitleAction } from "@/apis/hooks";
import {
  useModal,
  useModalControl,
  usePayload,
  withModal,
} from "@/modules/modals";
import { createTask, dispatchTask } from "@/modules/task/utilities";
import { isMovie, submodProcessColor } from "@/utilities";
import { LOG } from "@/utilities/console";
import { useEnabledLanguages } from "@/utilities/languages";
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
import {
  ChangeEventHandler,
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
  Selector,
  SimpleTable,
} from "..";
import Language from "../bazarr/Language";
import { useCustomSelection } from "../tables/plugins";
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

const ColorTool: FunctionComponent<ToolModalProps> = ({ process }) => {
  const [selection, setSelection] = useState<Nullable<string>>(null);

  const Modal = useModal();

  const submit = useCallback(() => {
    if (selection) {
      const action = submodProcessColor(selection);
      process(action);
    }
  }, [selection, process]);

  const footer = (
    <Button disabled={selection === null} onClick={submit}>
      Save
    </Button>
  );

  return (
    <Modal title="Choose Color" footer={footer}>
      <Selector options={colorOptions} onChange={setSelection}></Selector>
    </Modal>
  );
};

const ColorToolModal = withModal(ColorTool, "color-tool");

const FrameRateTool: FunctionComponent<ToolModalProps> = ({ process }) => {
  const [from, setFrom] = useState<Nullable<number>>(null);
  const [to, setTo] = useState<Nullable<number>>(null);

  const canSave = from !== null && to !== null && from !== to;

  const Modal = useModal();

  const submit = useCallback(() => {
    if (canSave) {
      const action = submodProcessFrameRate(from, to);
      process(action);
    }
  }, [canSave, from, to, process]);

  const footer = (
    <Button disabled={!canSave} onClick={submit}>
      Save
    </Button>
  );

  return (
    <Modal title="Change Frame Rate" footer={footer}>
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
    </Modal>
  );
};

const FrameRateModal = withModal(FrameRateTool, "frame-rate-tool");

const TimeAdjustmentTool: FunctionComponent<ToolModalProps> = ({ process }) => {
  const [isPlus, setPlus] = useState(true);
  const [offset, setOffset] = useState<[number, number, number, number]>([
    0, 0, 0, 0,
  ]);

  const Modal = useModal();

  const updateOffset = useCallback(
    (idx: number): ChangeEventHandler<HTMLInputElement> => {
      return (e) => {
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

  const footer = (
    <Button disabled={!canSave} onClick={submit}>
      Save
    </Button>
  );

  return (
    <Modal title="Adjust Times" footer={footer}>
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
    </Modal>
  );
};

const TimeAdjustmentModal = withModal(TimeAdjustmentTool, "time-adjust-tool");

const TranslationTool: FunctionComponent<ToolModalProps> = ({ process }) => {
  const { data: languages } = useEnabledLanguages();

  const available = useMemo(
    () => languages.filter((v) => v.code2 in availableTranslation),
    [languages]
  );

  const Modal = useModal();

  const [selectedLanguage, setLanguage] =
    useState<Nullable<Language.Info>>(null);

  const submit = useCallback(() => {
    if (selectedLanguage) {
      process("translate", { language: selectedLanguage.code2 });
    }
  }, [selectedLanguage, process]);

  const footer = (
    <Button disabled={!selectedLanguage} onClick={submit}>
      Translate
    </Button>
  );
  return (
    <Modal title="Translation" footer={footer}>
      <Form.Label>
        Enabled languages not listed here are unsupported by Google Translate.
      </Form.Label>
      <LanguageSelector
        options={available}
        onChange={setLanguage}
      ></LanguageSelector>
    </Modal>
  );
};

const TranslationModal = withModal(TranslationTool, "translate-tool");

const CanSelectSubtitle = (item: TableColumnType) => {
  return item.path.endsWith(".srt");
};

const STM: FunctionComponent = () => {
  const payload = usePayload<SupportType[]>();
  const [selections, setSelections] = useState<TableColumnType[]>([]);

  const Modal = useModal({ size: "xl" });
  const { hide } = useModalControl();

  const { mutateAsync } = useSubtitleAction();

  const process = useCallback(
    (action: string, override?: Partial<FormType.ModifySubtitle>) => {
      LOG("info", "executing action", action);
      hide();
      const tasks = selections.map((s) => {
        const form: FormType.ModifySubtitle = {
          id: s.id,
          type: s.type,
          language: s.language,
          path: s.path,
          ...override,
        };
        return createTask(s.path, mutateAsync, { action, form });
      });

      dispatchTask(tasks, "modify-subtitles");
    },
    [hide, selections, mutateAsync]
  );

  const { show } = useModalControl();

  const columns: Column<TableColumnType>[] = useMemo<Column<TableColumnType>[]>(
    () => [
      {
        Header: "Language",
        accessor: "_language",
        Cell: ({ value }) => (
          <Badge variant="secondary">
            <Language.Text value={value} long></Language.Text>
          </Badge>
        ),
      },
      {
        id: "file",
        Header: "File",
        accessor: "path",
        Cell: ({ value }) => {
          const path = value;

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

  const footer = (
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
          <ActionButtonItem icon={faTextHeight}>Fix Uppercase</ActionButtonItem>
        </Dropdown.Item>
        <Dropdown.Item eventKey="reverse_rtl">
          <ActionButtonItem icon={faExchangeAlt}>Reverse RTL</ActionButtonItem>
        </Dropdown.Item>
        <Dropdown.Item onSelect={() => show(ColorToolModal)}>
          <ActionButtonItem icon={faPaintBrush}>Add Color</ActionButtonItem>
        </Dropdown.Item>
        <Dropdown.Item onSelect={() => show(FrameRateModal)}>
          <ActionButtonItem icon={faFilm}>Change Frame Rate</ActionButtonItem>
        </Dropdown.Item>
        <Dropdown.Item onSelect={() => show(TimeAdjustmentModal)}>
          <ActionButtonItem icon={faClock}>Adjust Times</ActionButtonItem>
        </Dropdown.Item>
        <Dropdown.Item onSelect={() => show(TranslationModal)}>
          <ActionButtonItem icon={faLanguage}>Translate</ActionButtonItem>
        </Dropdown.Item>
      </Dropdown.Menu>
    </Dropdown>
  );

  return (
    <Modal title="Subtitle Tools" footer={footer}>
      <SimpleTable
        emptyText="No External Subtitles Found"
        plugins={plugins}
        columns={columns}
        onSelect={setSelections}
        canSelect={CanSelectSubtitle}
        data={data}
      ></SimpleTable>
      <ColorToolModal process={process}></ColorToolModal>
      <FrameRateModal process={process}></FrameRateModal>
      <TimeAdjustmentModal process={process}></TimeAdjustmentModal>
      <TranslationModal process={process}></TranslationModal>
    </Modal>
  );
};

export default withModal(STM, "subtitle-tools");
