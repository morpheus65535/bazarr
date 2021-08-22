import {
  faCheck,
  faCircleNotch,
  faInfoCircle,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Button, Container, Form } from "react-bootstrap";
import { Column, TableUpdater } from "react-table";
import {
  AsyncButton,
  FileForm,
  LanguageSelector,
  MessageIcon,
  SimpleTable,
} from "..";
import BackgroundTask from "../../@modules/task";
import { createTask } from "../../@modules/task/utilites";
import { useProfileBy, useProfileItemsToLanguages } from "../../@redux/hooks";
import { EpisodesApi, SubtitlesApi } from "../../apis";
import { Selector } from "../inputs";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useModalInformation } from "./hooks";

enum State {
  Updating,
  Valid,
  Warning,
}

interface PendingSubtitle {
  file: File;
  state: State;
  instance?: Item.Episode;
}

type EpisodeMap = {
  [name: string]: Item.Episode;
};

interface SerieProps {
  episodes: readonly Item.Episode[];
}

export const TaskGroupName = "Uploading Subtitles...";

const SeriesUploadModal: FunctionComponent<SerieProps & BaseModalProps> = ({
  episodes,
  ...modal
}) => {
  const { payload, closeModal } = useModalInformation<Item.Series>(
    modal.modalKey
  );

  const [uploading, setUpload] = useState(false);

  const [pending, setPending] = useState<PendingSubtitle[]>([]);

  const profile = useProfileBy(payload?.profileId);

  const avaliableLanguages = useProfileItemsToLanguages(profile);

  const [language, setLanguage] = useState<Language.Info | null>(null);

  useEffect(() => {
    if (avaliableLanguages.length > 0) {
      setLanguage(avaliableLanguages[0]);
    }
  }, [avaliableLanguages]);

  const filelist = useMemo(() => pending.map((v) => v.file), [pending]);

  const checkEpisodes = useCallback(
    async (list: PendingSubtitle[]) => {
      const names = list.map((v) => v.file.name);

      if (names.length > 0) {
        const results = await SubtitlesApi.info(names);

        const episodeMap = results.reduce<EpisodeMap>((prev, curr) => {
          const ep = episodes.find(
            (v) => v.season === curr.season && v.episode === curr.episode
          );
          if (ep) {
            prev[curr.filename] = ep;
          }
          return prev;
        }, {});

        setPending((pd) =>
          pd.map((v) => ({
            ...v,
            state: State.Valid,
            instance: episodeMap[v.file.name],
          }))
        );
      }
    },
    [episodes]
  );

  const setFiles = useCallback(
    (files: File[]) => {
      // At lease 1 language is required
      const list: PendingSubtitle[] = files.map((f) => {
        return {
          file: f,
          didCheck: false,
          state: State.Updating,
        };
      });
      setPending(list);
      checkEpisodes(list);
    },
    [checkEpisodes]
  );

  const uploadSubtitles = useCallback(async () => {
    if (payload === null || language === null) {
      return;
    }

    const { sonarrSeriesId: seriesid } = payload;
    const { code2, hi, forced } = language;

    const tasks = pending
      .filter((v) => v.instance !== undefined)
      .map((v) => {
        const { sonarrEpisodeId: episodeid } = v.instance!;

        const form: FormType.UploadSubtitle = {
          file: v.file,
          language: code2,
          hi: hi ?? false,
          forced: forced ?? false,
        };

        return createTask(
          v.file.name,
          seriesid,
          EpisodesApi.uploadSubtitles.bind(EpisodesApi),
          seriesid,
          episodeid,
          form
        );
      });

    BackgroundTask.dispatch(TaskGroupName, tasks);
  }, [payload, pending, language]);

  const canUpload = useMemo(
    () =>
      pending.length > 0 &&
      pending.every((v) => v.instance !== undefined) &&
      language,
    [pending, language]
  );

  const showTable = pending.length > 0;

  const columns = useMemo<Column<PendingSubtitle>[]>(
    () => [
      {
        id: "Icon",
        accessor: "state",
        className: "text-center",
        Cell: ({ value: state }) => {
          let icon = faCircleNotch;
          let color: string | undefined = undefined;
          let spin = false;
          let msgs: string[] = [];

          switch (state) {
            case State.Valid:
              icon = faCheck;
              color = "var(--success)";
              break;
            case State.Warning:
              icon = faInfoCircle;
              color = "var(--warning)";
              break;
            case State.Updating:
              spin = true;
              break;
            default:
              break;
          }

          return (
            <MessageIcon
              messages={msgs}
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
        Header: "Episode",
        accessor: "instance",
        className: "vw-1",
        Cell: ({ value, loose, row, externalUpdate }) => {
          const uploading = loose![0] as boolean;
          const availables = loose![1] as Item.Episode[];

          const options = availables.map<SelectorOption<Item.Episode>>(
            (ep) => ({
              label: `(${ep.season}x${ep.episode}) ${ep.title}`,
              value: ep,
            })
          );

          const change = useCallback(
            (ep: Nullable<Item.Episode>) => {
              if (ep) {
                const newInfo = { ...row.original };
                newInfo.instance = ep;
                externalUpdate && externalUpdate(row, newInfo);
              }
            },
            [row, externalUpdate]
          );

          return (
            <Selector
              disabled={uploading}
              options={options}
              value={value ?? null}
              onChange={change}
            ></Selector>
          );
        },
      },
      {
        accessor: "file",
        Cell: ({ row, externalUpdate, loose }) => {
          const [uploading] = loose!;
          return (
            <Button
              size="sm"
              variant="light"
              disabled={uploading}
              onClick={() => {
                externalUpdate && externalUpdate(row);
              }}
            >
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    []
  );

  const updateItem = useCallback<TableUpdater<PendingSubtitle>>(
    (row, info?: PendingSubtitle) => {
      setPending((pd) => {
        const newPending = [...pd];
        if (info) {
          newPending[row.index] = info;
        } else {
          newPending.splice(row.index, 1);
        }
        return newPending;
      });
    },
    []
  );

  const footer = (
    <div className="d-flex flex-row flex-grow-1 justify-content-between">
      <div className="w-25">
        <LanguageSelector
          disabled={uploading}
          options={avaliableLanguages}
          value={language}
          onChange={(l) => {
            if (l) {
              setLanguage(l);
            }
          }}
        ></LanguageSelector>
      </div>
      <div>
        <Button
          hidden={uploading}
          disabled={pending.length === 0}
          variant="outline-secondary"
          className="mr-2"
          onClick={() => setFiles([])}
        >
          Clean
        </Button>
        <AsyncButton
          disabled={!canUpload}
          onChange={setUpload}
          promise={uploadSubtitles}
          onSuccess={() => {
            closeModal();
            setFiles([]);
          }}
        >
          Upload
        </AsyncButton>
      </div>
    </div>
  );

  return (
    <BaseModal
      size="lg"
      title="Upload Subtitles"
      closeable={!uploading}
      footer={footer}
      {...modal}
    >
      <Container fluid className="flex-column">
        <Form>
          <Form.Group>
            <FileForm
              emptyText="Select..."
              disabled={showTable || avaliableLanguages.length === 0}
              multiple
              value={filelist}
              onChange={setFiles}
            ></FileForm>
          </Form.Group>
        </Form>
        <div hidden={!showTable}>
          <SimpleTable
            columns={columns}
            data={pending}
            loose={[uploading, episodes]}
            responsive={false}
            externalUpdate={updateItem}
          ></SimpleTable>
        </div>
      </Container>
    </BaseModal>
  );
};

export default SeriesUploadModal;
