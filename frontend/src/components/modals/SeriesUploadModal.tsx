import React, {
  FunctionComponent,
  useState,
  useMemo,
  useCallback,
  useEffect,
} from "react";
import { connect } from "react-redux";
import { Column } from "react-table";
import { Container, Form, Button, InputGroup } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faCircleNotch,
  faInfoCircle,
  faCheck,
  faExclamationTriangle,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";

import BasicModal, { BasicModalProps } from "./BasicModal";

import { AsyncButton, FileForm, BasicTable, OverlayIcon } from "..";

import { EpisodesApi, UtilsApi } from "../../apis";
import { updateSeriesInfo } from "../../@redux/actions";

import LanguageSelector from "../LanguageSelector";
import { useCloseModal, useIsShow } from "./provider";

enum SubtitleState {
  update,
  valid,
  warning,
  error,
}

interface MovieProps {
  series: Series;
  episodesList: AsyncState<Map<number, Episode[]>>;
  avaliableLanguages: Language[];
  update: (id: number) => void;
}

function mapStateToProps({ system, series }: StoreState) {
  return {
    avaliableLanguages: system.enabledLanguage.items,
    episodesList: series.episodeList,
  };
}

const SeriesUploadModal: FunctionComponent<MovieProps & BasicModalProps> = (
  props
) => {
  const { series, episodesList, avaliableLanguages, update, ...modal } = props;

  const [uploading, setUpload] = useState(false);

  const closeModal = useCloseModal();

  const [subtitleInfoList, setSubtitleInfo] = useState<SubtitleInfo[]>([]);

  const [language, setLanguage] = useState<Language | undefined>(() => {
    const lang = series.languages.length > 0 ? series.languages[0] : undefined;
    if (lang) {
      return avaliableLanguages.find((v) => v.code2 === lang.code2);
    }
    return undefined;
  });

  const filelist = useMemo(() => subtitleInfoList.map((v) => v.file), [
    subtitleInfoList,
  ]);

  const episodes = useMemo(
    () => episodesList.items.get(series.sonarrSeriesId) ?? [],
    [episodesList, series.sonarrSeriesId]
  );

  const [maxSeason, maxEpisode] = useMemo(() => {
    const season = episodes.reduce((v, e) => Math.max(v, e.season), 0);
    const episode = episodes.reduce((v, e) => Math.max(v, e.episode), 0);
    return [season, episode];
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
        !info.instance ||
        info.season !== info.instance.season ||
        info.episode !== info.instance.episode
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

  const show = useIsShow(modal.modalKey);

  useEffect(() => {
    if (show) {
      setFiles([]);
    }
  }, [show, setFiles]);

  const footer = useMemo(
    () => (
      <div className="d-flex flex-row flex-grow-1 justify-content-between">
        <LanguageSelector
          disabled={uploading}
          options={avaliableLanguages}
          defaultSelect={language}
          onChange={updateLanguage}
        ></LanguageSelector>
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
            success={() => {
              closeModal();
              update(series.sonarrSeriesId);
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
    <BasicModal
      size="lg"
      title={`Upload - ${series.title}`}
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
    </BasicModal>
  );
};

interface SubtitleInfo {
  file: File;
  state: SubtitleState;
  stateText: string[];
  season?: number;
  episode?: number;
  instance?: Episode;
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

  const removeItem = useCallback(
    (file: File) => {
      const idx = data.findIndex((v) => v.file === file);

      if (idx !== -1) {
        data.splice(idx, 1);

        update(data);
      }
    },
    [data, update]
  );

  const updateItem = useCallback(
    (info: SubtitleInfo) => {
      const idx = data.findIndex((v) => v.file === info.file);

      if (idx !== -1) {
        data[idx] = info;

        update(data);
      }
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
      UtilsApi.subtitleInfo(names)
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
            <OverlayIcon
              messages={stateText}
              color={color}
              icon={icon}
              spin={state === SubtitleState.update}
            ></OverlayIcon>
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
        Cell: (row) => {
          const info = row.row.original;
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
                    updateItem(info);
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
                    updateItem(info);
                  }
                }}
              ></Form.Control>
            </InputGroup>
          );
        },
      },
      {
        accessor: "file",
        Cell: (row) => {
          const info = row.row.original;
          return (
            <Button
              size="sm"
              variant="light"
              disabled={info.state === SubtitleState.update || uploading}
              onClick={() => {
                removeItem(row.value);
              }}
            >
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    [removeItem, maxSeason, maxEpisode, updateItem, uploading]
  );

  return (
    <BasicTable
      columns={columns}
      data={data}
      autoResetPage={false}
    ></BasicTable>
  );
};

export default connect(mapStateToProps, { update: updateSeriesInfo })(
  SeriesUploadModal
);
