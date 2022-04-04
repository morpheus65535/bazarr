import { useModal, useModalControl } from "@/modules/modals";
import { BuildKey } from "@/utilities";
import { LOG } from "@/utilities/console";
import {
  faCheck,
  faCircleNotch,
  faInfoCircle,
  faTimes,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Button, Container, Form } from "@mantine/core";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Column } from "react-table";
import { LanguageSelector, MessageIcon } from "..";
import { FileForm } from "../inputs";
import { SimpleTable } from "../tables";

type ModifyFn<T> = (index: number, info?: PendingSubtitle<T>) => void;

const RowContext = createContext<ModifyFn<unknown>>(() => {
  LOG("error", "RowContext not initialized");
});

export function useRowMutation() {
  return useContext(RowContext);
}

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

interface Props<T = unknown> {
  initial: T;
  availableLanguages: Language.Info[];
  upload: (items: PendingSubtitle<T>[]) => void;
  update: (items: PendingSubtitle<T>[]) => Promise<PendingSubtitle<T>[]>;
  validate: Validator<T>;
  columns: Column<PendingSubtitle<T>>[];
  hideAllLanguages?: boolean;
}

function SubtitleUploader<T>(props: Props<T>) {
  const {
    initial,
    columns,
    upload,
    update,
    validate,
    availableLanguages,
    hideAllLanguages,
  } = props;

  const [pending, setPending] = useState<PendingSubtitle<T>[]>([]);

  const showTable = pending.length > 0;

  const Modal = useModal({
    size: showTable ? "xl" : "lg",
  });

  const { hide } = useModalControl();

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

  const modify = useCallback(
    (index: number, info?: PendingSubtitle<T>) => {
      setPending((pd) => {
        const newPending = [...pd];
        if (info) {
          info = { ...info, ...validate(info) };
          newPending[index] = info;
        } else {
          newPending.splice(index, 1);
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
        Cell: ({ row, value }) => {
          const { original, index } = row;
          const mutate = useRowMutation();
          return (
            <Form.Check
              custom
              disabled={original.state === "fetching"}
              id={BuildKey(index, original.file.name, "hi")}
              checked={value}
              onChange={(v) => {
                const newInfo = { ...row.original };
                newInfo.hi = v.target.checked;
                mutate(row.index, newInfo);
              }}
            ></Form.Check>
          );
        },
      },
      {
        id: "forced",
        Header: "Forced",
        accessor: "forced",
        Cell: ({ row, value }) => {
          const { original, index } = row;
          const mutate = useRowMutation();
          return (
            <Form.Check
              custom
              disabled={original.state === "fetching"}
              id={BuildKey(index, original.file.name, "forced")}
              checked={value}
              onChange={(v) => {
                const newInfo = { ...row.original };
                newInfo.forced = v.target.checked;
                mutate(row.index, newInfo);
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
        Cell: ({ row, value }) => {
          const mutate = useRowMutation();
          return (
            <LanguageSelector
              disabled={row.original.state === "fetching"}
              options={availableLanguages}
              value={value}
              onChange={(lang) => {
                if (lang) {
                  const newInfo = { ...row.original };
                  newInfo.language = lang;
                  mutate(row.index, newInfo);
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
        Cell: ({ row }) => {
          const mutate = useRowMutation();
          return (
            <Button
              size="sm"
              color="light"
              disabled={row.original.state === "fetching"}
              onClick={() => {
                mutate(row.index);
              }}
            >
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    [columns, availableLanguages]
  );

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
          color="outline-secondary"
          className="mr-2"
          onClick={() => setFiles([])}
        >
          Clean
        </Button>
        <Button
          disabled={!canUpload || !showTable}
          onClick={() => {
            upload(pending);
            setFiles([]);
            hide();
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
    <Modal title="Update Subtitles" footer={footer}>
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
          <RowContext.Provider value={modify as ModifyFn<unknown>}>
            <SimpleTable
              columns={columnsWithAction}
              data={pending}
              responsive={false}
            ></SimpleTable>
          </RowContext.Provider>
        </div>
      </Container>
    </Modal>
  );
}

export default SubtitleUploader;
