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
import { Button, Container, Form, InputGroup } from "react-bootstrap";
import { connect } from "react-redux";
import { Column, TableUpdater } from "react-table";
import {
  AsyncButton,
  FileForm,
  LanguageSelector,
  MessageIcon,
  SimpleTable,
  useCloseModal,
  usePayload,
  useWhenModalShow,
} from "..";
import { seriesUpdateInfoAll } from "../../@redux/actions";
import { EpisodesApi, SubtitlesApi } from "../../apis";
import { useGetLanguage, useProfileBy } from "../../utilites";
import BaseModal, { BaseModalProps } from "./BaseModal";

enum SubtitleState {
  update,
  valid,
  warning,
  error,
}

interface MovieProps {
  episodesList: AsyncState<Map<number, Item.Episode[]>>;
  avaliableLanguages: Language[];
  update: (id: number) => void;
}

function mapStateToProps({ system, series }: ReduxStore) {
  return {
    avaliableLanguages: system.enabledLanguage.items,
    episodesList: series.episodeList,
  };
}

const SeriesUploadModal: FunctionComponent<MovieProps & BaseModalProps> = (
  props
) => {
  const { episodesList, avaliableLanguages, update, ...modal } = props;

  const series = usePayload<Item.Series>(modal.modalKey);

  const [uploading, setUpload] = useState(false);

  const closeModal = useCloseModal();

  const [subtitleInfoList, setSubtitleInfo] = useState<SubtitleInfo[]>([]);

  const [language, setLanguage] = useState<Language | undefined>(undefined);

  const profile = useProfileBy(series?.profileId);

  const languageGetter = useGetLanguage(true);

  useWhenModalShow(modal.modalKey, () => {
    if (profile) {
      const first = profile.items[0]?.language;
      const lang = languageGetter(first);
      setLanguage(lang);
    }
  });

  const filelist = useMemo(() => subtitleInfoList.map((v) => v.file), [
    subtitleInfoList,
  ]);

  const episodes = useMemo(() => {
    if (series) {
      return episodesList.items.get(series.sonarrSeriesId) ?? [];
    }
    return undefined;
  }, [episodesList, series]);

  const [maxSeason, maxEpisode] = useMemo(() => {
    if (episodes) {
      const season = episodes.reduce((v, e) => Math.max(v, e.season), 0);
      const episode = episodes.reduce((v, e) => Math.max(v, e.episode), 0);
      return [season, episode];
    }
    return [0, 0];
  }, [episodes]);

  const validItem = useCallback(
    (info: SubtitleInfo, lang?: Language) => {
      info.stateText = [];
      if (info.state === SubtitleState.update) {
        return;
      }

      if (!info.episode || !info.season) {
        info.stateText.push("Season or episode info is missing");
        info.state = SubtitleState.error;
        return;
      }

      if (
        episodes &&
        (!info.instance ||
          info.season !== info.instance.season ||
          info.episode !== info.instance.episode)
      ) {
        info.instance = episodes.find(
          (e) => e.season === info.season && e.episode === info.episode
        );
      }

      if (!info.instance) {
        info.stateText.push("Cannot find episode for this subtitle");
        info.state = SubtitleState.error;
        return;
      }

      if (
        info.episode > maxEpisode ||
        info.season > maxSeason ||
        info.episode <= 0 ||
        info.season <= 0
      ) {
        info.state = SubtitleState.error;
        info.stateText.push("Cannot find episode for this subtitle");
        return;
      }

      if (
        info.instance.subtitles &&
        info.instance.subtitles.find((s) => s.code2 === lang?.code2)
      ) {
        info.stateText.push("Overwrite existing subtitle");
      }

      if (info.stateText.length !== 0) {
        info.state = SubtitleState.warning;
      } else {
        info.state = SubtitleState.valid;
      }
    },
    [maxSeason, maxEpisode, episodes]
  );

  const updateLanguage = useCallback(
    (lang?: Language) => {
      setLanguage(lang);

      subtitleInfoList.forEach((v) => validItem(v, lang));
      setSubtitleInfo(subtitleInfoList);
    },
    [subtitleInfoList, validItem]
  );

  const setFiles = useCallback((list: File[]) => {
    const infoList: SubtitleInfo[] = list.map((f) => {
      return {
        file: f,
        state: SubtitleState.update,
        stateText: [],
      };
    });

    setSubtitleInfo(infoList);
  }, []);

  const updateSubtitleInfo = useCallback(
    (list: SubtitleInfo[], process: boolean = true) => {
      const newList = [...list];
      if (process) {
        newList.forEach((v) => validItem(v, language));
      }
      setSubtitleInfo(newList);
    },
    [validItem, language]
  );

  const uploadSubtitles = useCallback(
    async (list: SubtitleInfo[]) => {
      if (series === undefined) {
        return;
      }

      const { sonarrSeriesId } = series;
      const langCode = language?.code2;

      if (langCode) {
        list.forEach((v) => {
          v.state = SubtitleState.update;
          v.stateText = [];
        });
        updateSubtitleInfo(list, false);

        for (const info of list) {
          if (info.instance) {
            const { sonarrEpisodeId } = info.instance;
            await EpisodesApi.uploadSubtitles(sonarrSeriesId, sonarrEpisodeId, {
              file: info.file,
              language: langCode,
              // TODO
              hi: false,
              forced: false,
            });

            list.find((i) => i === info)!.state = SubtitleState.valid;
            updateSubtitleInfo(list, false);
          }
        }
      }
    },
    [series, language, updateSubtitleInfo]
  );

  const tableShow = subtitleInfoList.length !== 0;

  const isValid = useMemo(
    () =>
      subtitleInfoList.every(
        (v) =>
          v.state === SubtitleState.valid || v.state === SubtitleState.warning
      ),
    [subtitleInfoList]
  );

  const canUpload = tableShow && isValid && language?.code2 !== undefined;

  useWhenModalShow(modal.modalKey, () => {
    setFiles([]);
  });

  const footer = useMemo(
    () => (
      <div className="d-flex flex-row flex-grow-1 justify-content-between">
        <div className="w-25">
          <LanguageSelector
            disabled={uploading}
            options={avaliableLanguages}
            value={language}
            onChange={updateLanguage}
          ></LanguageSelector>
        </div>
        <div>
          <Button
            hidden={!tableShow || uploading}
            variant="outline-secondary"
            className="mr-2"
            onClick={() => setFiles([])}
          >
            Clean
          </Button>
          <AsyncButton
            disabled={!canUpload}
            onChange={setUpload}
            promise={() => uploadSubtitles(subtitleInfoList)}
            onSuccess={() => {
              closeModal();
              update(series!.sonarrSeriesId);
            }}
          >
            Upload
          </AsyncButton>
        </div>
      </div>
    ),
    [
      uploading,
      avaliableLanguages,
      language,
      tableShow,
      setFiles,
      canUpload,
      series,
      subtitleInfoList,
      update,
      uploadSubtitles,
      updateLanguage,
      closeModal,
    ]
  );

  return (
    <BaseModal
      size="lg"
      title={`Upload - ${series?.title}`}
      closeable={!uploading}
      footer={footer}
      {...modal}
    >
      <Container fluid className="flex-column">
        <Form>
          <Form.Group>
            <FileForm
              emptyText="Select..."
              disabled={tableShow}
              multiple
              files={filelist}
              onChange={setFiles}
            ></FileForm>
          </Form.Group>
        </Form>
        <div hidden={!tableShow}>
          <Table
            uploading={uploading}
            maxSeason={maxSeason}
            maxEpisode={maxEpisode}
            data={subtitleInfoList}
            update={updateSubtitleInfo}
          ></Table>
        </div>
      </Container>
    </BaseModal>
  );
};

interface SubtitleInfo {
  file: File;
  state: SubtitleState;
  stateText: string[];
  season?: number;
  episode?: number;
  instance?: Item.Episode;
}

interface TableProps {
  maxSeason: number;
  maxEpisode: number;
  data: SubtitleInfo[];
  uploading: boolean;
  update: (info: SubtitleInfo[]) => void;
}

const Table: FunctionComponent<TableProps> = (props) => {
  const { maxSeason, maxEpisode, data, update, uploading } = props;

  const updateItem = useCallback<TableUpdater<SubtitleInfo>>(
    (row, info?: SubtitleInfo) => {
      if (info) {
        data[row.index] = info;
      } else {
        data.splice(row.index, 1);
      }
      update(data);
    },
    [data, update]
  );

  useEffect(() => {
    if (uploading) return;

    const names = data.flatMap((v) => {
      if (v.state === SubtitleState.update) {
        return v.file.name;
      } else {
        return [];
      }
    });

    if (names.length !== 0) {
      SubtitlesApi.info(names)
        .then((result) => {
          result.forEach((v) => {
            const idx = data.findIndex((d) => d.file.name === v.filename);

            if (idx !== -1) {
              data[idx].season = v.season;
              data[idx].episode = v.episode;
            }
          });
        })
        .catch(() => {
          // TODO
        })
        .finally(() => {
          data.forEach((v) => (v.state = SubtitleState.warning));
          update(data);
        });
    }
  }, [uploading, data, update]);

  const columns = useMemo<Column<SubtitleInfo>[]>(
    () => [
      {
        accessor: "state",
        className: "text-center",
        Cell: (row) => {
          const state = row.value;
          const { stateText } = row.row.original;

          let icon;
          let color;
          if (state === SubtitleState.error) {
            icon = faExclamationTriangle;
            color = "var(--danger)";
          } else if (state === SubtitleState.valid) {
            icon = faCheck;
            color = "var(--success)";
          } else if (state === SubtitleState.warning) {
            icon = faInfoCircle;
            color = "var(--warning)";
          } else {
            icon = faCircleNotch;
            color = undefined;
          }

          return (
            <MessageIcon
              messages={stateText}
              color={color}
              icon={icon}
              spin={state === SubtitleState.update}
            ></MessageIcon>
          );
        },
      },
      {
        Header: "File",
        accessor: (d) => d.file.name,
      },
      {
        Header: "Season / Episode",
        accessor: "season",
        Cell: ({ row, update }) => {
          const info = row.original;
          const season = info.season;
          const episode = info.episode;
          return (
            <InputGroup className="d-flex flex-nowrap">
              <Form.Control
                style={{ maxWidth: 72, minWidth: 56 }}
                disabled={info.state === SubtitleState.update || uploading}
                isInvalid={
                  season ? season > maxSeason || season <= 0 : undefined
                }
                type="text"
                defaultValue={season}
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  const v = Number.parseInt(e.target.value);
                  if (!Number.isNaN(v) && v !== season) {
                    info.season = v;
                    update && update(row, info);
                  }
                }}
              ></Form.Control>
              <Form.Control
                style={{ maxWidth: 96, minWidth: 56 }}
                disabled={info.state === SubtitleState.update || uploading}
                isInvalid={
                  episode ? episode > maxEpisode || episode <= 0 : false
                }
                type="text"
                defaultValue={episode}
                onBlur={(e: React.FocusEvent<HTMLInputElement>) => {
                  const v = Number.parseInt(e.target.value);
                  if (!Number.isNaN(v) && v !== episode) {
                    info.episode = v;
                    update && update(row, info);
                  }
                }}
              ></Form.Control>
            </InputGroup>
          );
        },
      },
      {
        accessor: "file",
        Cell: ({ row, update }) => {
          const info = row.original;
          return (
            <Button
              size="sm"
              variant="light"
              disabled={info.state === SubtitleState.update || uploading}
              onClick={() => {
                update && update(row);
              }}
            >
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    [maxSeason, maxEpisode, uploading]
  );

  return (
    <SimpleTable
      columns={columns}
      data={data}
      update={updateItem}
    ></SimpleTable>
  );
};

export default connect(mapStateToProps, { update: seriesUpdateInfoAll })(
  SeriesUploadModal
);
