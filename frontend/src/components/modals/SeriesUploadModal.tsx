import {
  faCheck,
  faCircleNotch,
  faExclamationTriangle,
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
  useCloseModal,
  usePayload,
} from "..";
import { useProfileBy, useProfileItemsToLanguages } from "../../@redux/hooks";
import { EpisodesApi, SubtitlesApi } from "../../apis";
import { Selector } from "../inputs";
import BaseModal, { BaseModalProps } from "./BaseModal";

enum State {
  Update,
  Valid,
  Warning,
  Error,
}

interface PendingSubtitle {
  file: File;
  didCheck: boolean;
  instance?: Item.Episode;
}

type SubtitleState = {
  state: State;
  infos: string[];
};

type ProcessState = {
  [name: string]: SubtitleState;
};

type EpisodeMap = {
  [name: string]: Item.Episode;
};

interface SerieProps {
  episodes: readonly Item.Episode[];
}

const SeriesUploadModal: FunctionComponent<SerieProps & BaseModalProps> = ({
  episodes,
  ...modal
}) => {
  const series = usePayload<Item.Series>(modal.modalKey);

  const [uploading, setUpload] = useState(false);

  const closeModal = useCloseModal();

  const [pending, setPending] = useState<PendingSubtitle[]>([]);

  const [processState, setProcessState] = useState<ProcessState>({});

  const profile = useProfileBy(series?.profileId);

  const avaliableLanguages = useProfileItemsToLanguages(profile);

  const [language, setLanguage] = useState<Language.Info | null>(null);

  useEffect(() => {
    if (avaliableLanguages.length > 0) {
      setLanguage(avaliableLanguages[0]);
    }
  }, [avaliableLanguages]);

  const filelist = useMemo(() => pending.map((v) => v.file), [pending]);

  // Vaildate
  useEffect(() => {
    const states = pending.reduce<ProcessState>((prev, info) => {
      const subState: SubtitleState = {
        state: State.Valid,
        infos: [],
      };

      const { file, instance } = info;

      if (!info.didCheck) {
        subState.state = State.Update;
      } else if (!instance) {
        subState.infos.push("Season or episode info is missing");
        subState.state = State.Error;
      } else {
        if (
          instance.subtitles.find((v) => v.code2 === language?.code2) !==
          undefined
        ) {
          subState.infos.push("Overwrite existing subtitle");
          subState.state = State.Warning;
        }
      }

      prev[file.name] = subState;
      return prev;
    }, {});

    setProcessState(states);
  }, [pending, language?.code2]);

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
            didCheck: true,
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
        };
      });
      setPending(list);

      const states = files.reduce<ProcessState>(
        (v, curr) => ({
          ...v,
          [curr.name]: { state: State.Update, infos: [] },
        }),
        {}
      );
      setProcessState(states);
      checkEpisodes(list);
    },
    [checkEpisodes]
  );

  const uploadSubtitles = useCallback(async () => {
    if (series === null || language === null) {
      return;
    }

    const { sonarrSeriesId: seriesid } = series;

    let uploadStates = pending.reduce<ProcessState>((prev, curr) => {
      prev[curr.file.name] = { state: State.Update, infos: [] };
      return prev;
    }, {});

    setProcessState(uploadStates);

    let exception = false;

    for (const info of pending) {
      if (info.instance) {
        const { sonarrEpisodeId: episodeid } = info.instance;
        const { file } = info;
        const { code2, hi, forced } = language;

        try {
          const form: FormType.UploadSubtitle = {
            file,
            language: code2,
            hi: hi ?? false,
            forced: forced ?? false,
          };

          await EpisodesApi.uploadSubtitles(seriesid, episodeid, form);

          uploadStates = {
            ...uploadStates,
            [info.file.name]: { state: State.Valid, infos: [] },
          };
        } catch (error) {
          uploadStates = {
            ...uploadStates,
            [info.file.name]: { state: State.Error, infos: [] },
          };
          exception = true;
        }

        setProcessState(uploadStates);
      }
    }

    if (exception) {
      throw new Error("Error when uploading subtitles");
    }
  }, [series, pending, language]);

  const canUpload = useMemo(
    () =>
      pending.length > 0 &&
      pending.every((v) => v.instance !== undefined) &&
      language,
    [pending, language]
  );

  const tableShow = pending.length > 0;

  const columns = useMemo<Column<PendingSubtitle>[]>(
    () => [
      {
        id: "Icon",
        accessor: "instance",
        className: "text-center",
        Cell: ({ row, loose }) => {
          const { file } = row.original;

          const name = file.name;
          const states = loose![1] as ProcessState;

          let icon = faCircleNotch;
          let color: string | undefined = undefined;
          let spin = false;
          let msgs: string[] = [];

          if (name in states) {
            const state = states[name];
            msgs = state.infos;
            switch (state.state) {
              case State.Error:
                icon = faExclamationTriangle;
                color = "var(--danger)";
                break;
              case State.Valid:
                icon = faCheck;
                color = "var(--success)";
                break;
              case State.Warning:
                icon = faInfoCircle;
                color = "var(--warning)";
                break;
              case State.Update:
                spin = true;
                break;
              default:
                break;
            }
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
          const availables = loose![2] as Item.Episode[];

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
              disabled={tableShow || avaliableLanguages.length === 0}
              multiple
              value={filelist}
              onChange={setFiles}
            ></FileForm>
          </Form.Group>
        </Form>
        <div hidden={!tableShow}>
          <SimpleTable
            columns={columns}
            data={pending}
            loose={[uploading, processState, episodes]}
            responsive={false}
            externalUpdate={updateItem}
          ></SimpleTable>
        </div>
      </Container>
    </BaseModal>
  );
};

export default SeriesUploadModal;
