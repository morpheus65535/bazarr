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
import { useSelector } from "react-redux";
import { Column } from "react-table";
import {
  ActionIcon,
  ActionIconItem,
  LanguageSelector,
  LanguageText,
  Selector,
  SimpleTable,
  usePayload,
  useShowModal,
} from "..";
import { SubtitlesApi } from "../../apis";
import { colorOptions } from "../../Settings/Subtitles/options";
import { isMovie, submodProcessColor } from "../../utilites";
import { AsyncButton } from "../buttons";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useCloseModal } from "./provider";
import { avaliableTranslation } from "./toolOptions";

type SupportType = Item.Episode | Item.Movie;

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

const AddColorModal: FunctionComponent<BaseModalProps> = (props) => {
  const { ...modal } = props;
  const [updating, setUpdate] = useState(false);
  const [selection, setSelection] = useState<Nullable<string>>(null);

  const item = usePayload<SupportType>(modal.modalKey, 1);
  const subtitle = usePayload<Subtitle>(modal.modalKey);
  const closeModal = useCloseModal();

  const submit = useCallback(() => {
    if (subtitle && subtitle.path && selection && item) {
      const [id, type] = getIdAndType(item);
      return SubtitlesApi.modify(
        selection,
        id,
        type,
        subtitle.code2,
        subtitle.path
      );
    } else {
      return null;
    }
  }, [selection, subtitle, item]);

  const footer = useMemo(
    () => (
      <AsyncButton
        disabled={selection === null}
        promise={submit}
        onSuccess={closeModal}
        onChange={setUpdate}
      >
        Save
      </AsyncButton>
    ),
    [selection, submit, closeModal]
  );
  return (
    <BaseModal
      title="Choose Color"
      footer={footer}
      closeable={!updating}
      {...modal}
    >
      <Selector
        disabled={updating}
        options={colorOptions}
        onChange={(s) => {
          if (s) {
            s = submodProcessColor(s);
          }
          setSelection(s);
        }}
      ></Selector>
    </BaseModal>
  );
};

const ChangeFrameRateModal: FunctionComponent<BaseModalProps> = (props) => {
  const { ...modal } = props;

  const [updating, setUpdate] = useState(false);

  const [from, setFrom] = useState<Nullable<number>>(null);
  const [to, setTo] = useState<Nullable<number>>(null);

  const item = usePayload<SupportType>(modal.modalKey, 1);
  const subtitle = usePayload<Subtitle>(modal.modalKey);
  const closeModal = useCloseModal();

  const canSave = from !== null && to !== null && from !== to;

  const submit = useCallback(() => {
    if (canSave && subtitle && subtitle.path && item) {
      const action = submodProcessFrameRate(from!, to!);
      const [id, type] = getIdAndType(item);
      return SubtitlesApi.modify(
        action,
        id,
        type,
        subtitle.code2,
        subtitle.path
      );
    } else {
      return null;
    }
  }, [subtitle, canSave, from, to, item]);

  const footer = useMemo(
    () => (
      <AsyncButton
        disabled={!canSave}
        promise={submit}
        onSuccess={closeModal}
        onChange={setUpdate}
      >
        Save
      </AsyncButton>
    ),
    [submit, closeModal, canSave]
  );

  return (
    <BaseModal
      title="Change Frame Rate"
      footer={footer}
      closeable={!updating}
      {...modal}
    >
      <InputGroup className="px-2">
        <Form.Control
          disabled={updating}
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
          disabled={updating}
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

const AdjustTimesModal: FunctionComponent<BaseModalProps> = (props) => {
  const { ...modal } = props;

  const [updating, setUpdate] = useState(false);
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

  const item = usePayload<SupportType>(modal.modalKey, 1);
  const subtitle = usePayload<Subtitle>(modal.modalKey);
  const closeModal = useCloseModal();

  const canSave = offset.some((v) => v !== 0);

  const submit = useCallback(() => {
    if (canSave && subtitle && subtitle.path && item) {
      const newOffset = offset.map((v) => (isPlus ? v : -v));
      const action = submodProcessOffset(
        newOffset[0],
        newOffset[1],
        newOffset[2],
        newOffset[3]
      );
      const [id, type] = getIdAndType(item);
      return SubtitlesApi.modify(
        action,
        id,
        type,
        subtitle.code2,
        subtitle.path
      );
    } else {
      return null;
    }
  }, [subtitle, canSave, offset, isPlus, item]);

  const footer = useMemo(
    () => (
      <AsyncButton
        disabled={!canSave}
        promise={submit}
        onSuccess={closeModal}
        onChange={setUpdate}
      >
        Save
      </AsyncButton>
    ),
    [submit, closeModal, canSave]
  );

  return (
    <BaseModal
      title="Adjust Times"
      footer={footer}
      closeable={!updating}
      {...modal}
    >
      <InputGroup>
        <InputGroup.Prepend>
          <Button
            disabled={updating}
            variant="secondary"
            title={isPlus ? "Later" : "Earlier"}
            onClick={() => setPlus(!isPlus)}
          >
            <FontAwesomeIcon icon={isPlus ? faPlus : faMinus}></FontAwesomeIcon>
          </Button>
        </InputGroup.Prepend>
        <Form.Control
          disabled={updating}
          type="number"
          placeholder="hour"
          onChange={updateOffset(0)}
        ></Form.Control>
        <Form.Control
          disabled={updating}
          type="number"
          placeholder="min"
          onChange={updateOffset(1)}
        ></Form.Control>
        <Form.Control
          disabled={updating}
          type="number"
          placeholder="sec"
          onChange={updateOffset(2)}
        ></Form.Control>
        <Form.Control
          disabled={updating}
          type="number"
          placeholder="ms"
          onChange={updateOffset(3)}
        ></Form.Control>
      </InputGroup>
    </BaseModal>
  );
};

interface TranslateProps {
  item?: SupportType;
}

const TranslateModal: FunctionComponent<BaseModalProps & TranslateProps> = ({
  ...modal
}) => {
  const item = usePayload<SupportType>(modal.modalKey, 1);
  const subtitle = usePayload<Subtitle>(modal.modalKey);

  const languages = useSelector<ReduxStore, Language[]>(
    (s) => s.system.enabledLanguage.items
  );

  const avaliable = useMemo(
    () =>
      languages.filter(
        (v) => v.code2 !== subtitle?.code2 && v.code2 in avaliableTranslation
      ),
    [subtitle, languages]
  );

  const [selectedLanguage, setLanguage] = useState<Nullable<Language>>(null);

  const submit = useCallback(() => {
    if (item && item.path && subtitle && subtitle.path && selectedLanguage) {
      const [id, type] = getIdAndType(item);
      return SubtitlesApi.modify(
        "translate",
        id,
        type,
        selectedLanguage.code2,
        subtitle.path
      );
    }
    return null;
  }, [item, subtitle, selectedLanguage]);

  const closeModal = useCloseModal();

  const footer = useMemo(
    () => (
      <AsyncButton
        disabled={!selectedLanguage}
        onSuccess={() => closeModal()}
        promise={submit}
      >
        Translate
      </AsyncButton>
    ),
    [submit, selectedLanguage, closeModal]
  );

  return (
    <BaseModal title="Translate Subtitle" footer={footer} {...modal}>
      <InputGroup className="mb-3">
        <InputGroup.Prepend>
          <InputGroup.Text>Original</InputGroup.Text>
        </InputGroup.Prepend>
        <Form.Control disabled value={subtitle?.name ?? ""}></Form.Control>
      </InputGroup>
      <LanguageSelector
        options={avaliable}
        onChange={setLanguage}
      ></LanguageSelector>
    </BaseModal>
  );
};

interface Props {
  item?: SupportType;
}

const Table: FunctionComponent<Props> = ({ item }) => {
  const submitAction = useCallback(
    (action: string, sub: Subtitle) => {
      if (sub.path && item) {
        const [id, type] = getIdAndType(item);
        setUpdate(true);
        setActive(sub.path);
        SubtitlesApi.modify(action, id, type, sub.code2, sub.path).finally(
          () => {
            setUpdate(false);
            setActive(null);
          }
        );
      }
    },
    [item]
  );

  const [updating, setUpdate] = useState<boolean>(false);
  const [active, setActive] = useState<Nullable<string>>(null);

  const syncSubtitle = useCallback(
    (sub: Subtitle) => {
      if (sub.path && item) {
        const [id, type] = getIdAndType(item);

        setUpdate(true);
        setActive(sub.path);
        SubtitlesApi.modify("sync", id, type, sub.code2, sub.path).finally(
          () => {
            setUpdate(false);
            setActive(null);
          }
        );
      }
    },
    [item]
  );

  const showModal = useShowModal();

  const columns: Column<Subtitle>[] = useMemo<Column<Subtitle>[]>(
    () => [
      {
        accessor: "name",
        Cell: ({ row }) => (
          <Badge variant="secondary">
            <LanguageText text={row.original} long={true}></LanguageText>
          </Badge>
        ),
      },
      {
        Header: "File Name",
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
      {
        Header: "Tools",
        accessor: "code2",
        Cell: (row) => {
          const sub = row.row.original;

          const isActive = sub.path !== null && sub.path === active;

          return (
            <Dropdown
              as={ButtonGroup}
              onSelect={(k) => k && submitAction(k, sub)}
            >
              <ActionIcon
                size="sm"
                loading={isActive}
                disabled={updating}
                icon={faPlay}
                onClick={() => syncSubtitle(sub)}
              >
                Sync
              </ActionIcon>
              <Dropdown.Toggle
                disabled={updating}
                split
                variant="light"
                size="sm"
                className="px-2"
              ></Dropdown.Toggle>
              <Dropdown.Menu>
                <Dropdown.Item eventKey="remove_HI">
                  <ActionIconItem icon={faDeaf}>Remove HI Tags</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="remove_tags">
                  <ActionIconItem icon={faCode}>
                    Remove Style Tags
                  </ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="OCR_fixes">
                  <ActionIconItem icon={faImage}>OCR Fixes</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="common">
                  <ActionIconItem icon={faMagic}>Common Fixes</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="fix_uppercase">
                  <ActionIconItem icon={faTextHeight}>
                    Fix Uppercase
                  </ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item eventKey="reverse_rtl">
                  <ActionIconItem icon={faExchangeAlt}>
                    Reverse RTL
                  </ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item onSelect={() => showModal("add-color", sub)}>
                  <ActionIconItem icon={faPaintBrush}>Add Color</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item
                  onSelect={() => showModal("change-frame-rate", sub)}
                >
                  <ActionIconItem icon={faFilm}>
                    Change Frame Rate
                  </ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item onSelect={() => showModal("adjust-times", sub)}>
                  <ActionIconItem icon={faClock}>Adjust Times</ActionIconItem>
                </Dropdown.Item>
                <Dropdown.Item onSelect={() => showModal("translate-sub", sub)}>
                  <ActionIconItem icon={faLanguage}>Translate</ActionIconItem>
                </Dropdown.Item>
              </Dropdown.Menu>
            </Dropdown>
          );
        },
      },
    ],
    [submitAction, updating, syncSubtitle, active, showModal]
  );

  const data: Subtitle[] = useMemo<Subtitle[]>(
    () => item?.subtitles.filter((val) => val.path !== null) ?? [],
    [item]
  );

  return (
    <SimpleTable
      emptyText="No External Subtitles Found"
      responsive={false}
      columns={columns}
      data={data}
    ></SimpleTable>
  );
};

const Tools: FunctionComponent<BaseModalProps> = (props) => {
  const item = usePayload<SupportType>(props.modalKey);
  return (
    <React.Fragment>
      <BaseModal title={`Tools - ${item?.title ?? ""}`} {...props}>
        <Table item={item ?? undefined} {...props}></Table>
      </BaseModal>
      <AddColorModal modalKey="add-color"></AddColorModal>
      <ChangeFrameRateModal modalKey="change-frame-rate"></ChangeFrameRateModal>
      <AdjustTimesModal modalKey="adjust-times"></AdjustTimesModal>
      <TranslateModal modalKey="translate-sub"></TranslateModal>
    </React.Fragment>
  );
};

export default Tools;
