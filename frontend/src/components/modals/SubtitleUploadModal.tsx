import {
  faCheck,
  faCircleNotch,
  faInfoCircle,
  faTimes,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button, Container, Form } from "react-bootstrap";
import { Column, TableUpdater } from "react-table";
import { LanguageSelector, MessageIcon } from "..";
import { BuildKey } from "../../utilities";
import { FileForm } from "../inputs";
import { SimpleTable } from "../tables";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useCloseModal } from "./hooks";

export interface PendingSubtitle<P> {
  file: File;
  state: "valid" | "fetching" | "warning" | "error";
  messages: string[];
  language: Language.Info | null;
  forced: boolean;
  hi: boolean;
  payload: P;
}

export type Validator<T> = (
  item: PendingSubtitle<T>
) => Pick<PendingSubtitle<T>, "state" | "messages">;

interface Props<T> {
  initial: T;
  availableLanguages: Language.Info[];
  upload: (items: PendingSubtitle<T>[]) => void;
  update: (items: PendingSubtitle<T>[]) => Promise<PendingSubtitle<T>[]>;
  validate: Validator<T>;
  columns: Column<PendingSubtitle<T>>[];
  hideAllLanguages?: boolean;
}

export default function SubtitleUploadModal<T>(
  props: Props<T> & Omit<BaseModalProps, "footer" | "title" | "size">
) {
  const {
    initial,
    columns,
    upload,
    update,
    validate,
    availableLanguages,
    hideAllLanguages,
  } = props;

  const closeModal = useCloseModal();

  const [pending, setPending] = useState<PendingSubtitle<T>[]>([]);

  const fileList = useMemo(() => pending.map((v) => v.file), [pending]);

  const initialRef = useRef(initial);

  const setFiles = useCallback(
    async (files: File[]) => {
      const initialLanguage =
        availableLanguages.length > 0 ? availableLanguages[0] : null;
      let list = files.map<PendingSubtitle<T>>((file) => ({
        file,
        state: "fetching",
        messages: [],
        language: initialLanguage,
        forced: false,
        hi: false,
        payload: { ...initialRef.current },
      }));

      if (update) {
        setPending(list);
        list = await update(list);
      } else {
        list = list.map<PendingSubtitle<T>>((v) => ({
          ...v,
          state: "valid",
        }));
      }

      list = list.map((v) => ({
        ...v,
        ...validate(v),
      }));

      setPending(list);
    },
    [update, validate, availableLanguages]
  );

  const modify = useCallback<TableUpdater<PendingSubtitle<T>>>(
    (row, info?: PendingSubtitle<T>) => {
      setPending((pd) => {
        const newPending = [...pd];
        if (info) {
          info = { ...info, ...validate(info) };
          newPending[row.index] = info;
        } else {
          newPending.splice(row.index, 1);
        }
        return newPending;
      });
    },
    [validate]
  );

  useEffect(() => {
    setPending((pd) => {
      const newPd = pd.map((v) => {
        if (v.state !== "fetching") {
          return { ...v, ...validate(v) };
        } else {
          return v;
        }
      });

      return newPd;
    });
  }, [validate]);

  const columnsWithAction = useMemo<Column<PendingSubtitle<T>>[]>(
    () => [
      {
        id: "icon",
        accessor: "state",
        className: "text-center",
        Cell: ({ value, row }) => {
          let icon = faCircleNotch;
          let color: string | undefined = undefined;
          let spin = false;

          switch (value) {
            case "fetching":
              spin = true;
              break;
            case "warning":
              icon = faInfoCircle;
              color = "var(--warning)";
              break;
            case "valid":
              icon = faCheck;
              color = "var(--success)";
              break;
            default:
              icon = faTimes;
              color = "var(--danger)";
              break;
          }

          const messages = row.original.messages;

          return (
            <MessageIcon
              messages={messages}
              color={color}
              icon={icon}
              spin={spin}
            ></MessageIcon>
          );
        },
      },
      {
        Header: "File",
        accessor: (d) => d.file.name,
      },
      {
        id: "hi",
        Header: "HI",
        accessor: "hi",
        Cell: ({ row, value, update }) => {
          const { original, index } = row;
          return (
            <Form.Check
              disabled={original.state === "fetching"}
              id={BuildKey(index, original.file.name, "hi")}
              checked={value}
              onChange={(v) => {
                const newInfo = { ...row.original };
                newInfo.hi = v.target.checked;
                update && update(row, newInfo);
              }}
            ></Form.Check>
          );
        },
      },
      {
        id: "forced",
        Header: "Forced",
        accessor: "forced",
        Cell: ({ row, value, update }) => {
          const { original, index } = row;
          return (
            <Form.Check
              disabled={original.state === "fetching"}
              id={BuildKey(index, original.file.name, "forced")}
              checked={value}
              onChange={(v) => {
                const newInfo = { ...row.original };
                newInfo.forced = v.target.checked;
                update && update(row, newInfo);
              }}
            ></Form.Check>
          );
        },
      },
      {
        id: "language",
        Header: "Language",
        accessor: "language",
        className: "w-25",
        Cell: ({ row, update, value }) => {
          return (
            <LanguageSelector
              disabled={row.original.state === "fetching"}
              options={availableLanguages}
              value={value}
              onChange={(lang) => {
                if (lang && update) {
                  const newInfo = { ...row.original };
                  newInfo.language = lang;
                  update(row, newInfo);
                }
              }}
            ></LanguageSelector>
          );
        },
      },
      ...columns,
      {
        id: "action",
        accessor: "file",
        Cell: ({ row, update }) => (
          <Button
            size="sm"
            variant="light"
            disabled={row.original.state === "fetching"}
            onClick={() => {
              update && update(row);
            }}
          >
            <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
          </Button>
        ),
      },
    ],
    [columns, availableLanguages]
  );

  const showTable = pending.length > 0;

  const canUpload = useMemo(
    () =>
      pending.length > 0 &&
      pending.every((v) => v.state === "valid" || v.state === "warning"),
    [pending]
  );

  const footer = (
    <div className="d-flex flex-row-reverse flex-grow-1 justify-content-between">
      <div>
        <Button
          hidden={!showTable}
          variant="outline-secondary"
          className="me-2"
          onClick={() => setFiles([])}
        >
          Clean
        </Button>
        <Button
          disabled={!canUpload || !showTable}
          onClick={() => {
            upload(pending);
            setFiles([]);
            closeModal();
          }}
        >
          Upload
        </Button>
      </div>
      <div className="w-25" hidden={hideAllLanguages}>
        <LanguageSelector
          options={availableLanguages}
          value={null}
          disabled={!showTable}
          onChange={(lang) => {
            if (lang) {
              setPending((pd) =>
                pd
                  .map((v) => ({ ...v, language: lang }))
                  .map((v) => ({ ...v, ...validate(v) }))
              );
            }
          }}
        ></LanguageSelector>
      </div>
    </div>
  );

  return (
    <BaseModal
      size={showTable ? "xl" : "lg"}
      title="Upload Subtitles"
      footer={footer}
      {...props}
    >
      <Container fluid className="flex-column">
        <Form>
          <Form.Group>
            <FileForm
              disabled={showTable}
              emptyText="Select..."
              multiple
              value={fileList}
              onChange={setFiles}
            ></FileForm>
          </Form.Group>
        </Form>
        <div hidden={!showTable}>
          <SimpleTable
            columns={columnsWithAction}
            data={pending}
            responsive={false}
            update={modify}
          ></SimpleTable>
        </div>
      </Container>
    </BaseModal>
  );
}
