import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";
import api from "src/apis/raw";
import {
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "src/utilities/languages";
import { dispatchTask } from "../../@modules/task";
import { createTask } from "../../@modules/task/utilities";
import { Selector } from "../inputs";
import { BaseModalProps } from "./BaseModal";
import { useModalInformation } from "./hooks";
import SubtitleUploadModal, {
  PendingSubtitle,
  Validator,
} from "./SubtitleUploadModal";

interface Payload {
  instance: Item.Episode | null;
}

interface SeriesProps {
  episodes: readonly Item.Episode[];
}

export const TaskGroupName = "Uploading Subtitles...";

const SeriesUploadModal: FunctionComponent<SeriesProps & BaseModalProps> = ({
  episodes,
  ...modal
}) => {
  const { payload } = useModalInformation<Item.Series>(modal.modalKey);

  const profile = useLanguageProfileBy(payload?.profileId);

  const availableLanguages = useProfileItemsToLanguages(profile);

  const update = useCallback(
    async (list: PendingSubtitle<Payload>[]) => {
      const newList = [...list];
      const names = list.map((v) => v.file.name);

      if (names.length > 0) {
        const results = await api.subtitles.info(names);

        // TODO: Optimization
        newList.forEach((v) => {
          const info = results.find((f) => f.filename === v.file.name);
          if (info) {
            v.payload.instance =
              episodes.find(
                (e) => e.season === info.season && e.episode === info.episode
              ) ?? null;
          }
        });
      }

      return newList;
    },
    [episodes]
  );

  const validate = useCallback<Validator<Payload>>((item) => {
    const { language } = item;
    const { instance } = item.payload;
    if (language === null || instance === null) {
      return {
        state: "error",
        messages: ["Language or Episode is not selected"],
      };
    } else if (
      instance.subtitles.find((v) => v.code2 === language.code2) !== undefined
    ) {
      return {
        state: "warning",
        messages: ["Override existing subtitle"],
      };
    }
    return {
      state: "valid",
      messages: [],
    };
  }, []);

  const upload = useCallback(
    (items: PendingSubtitle<Payload>[]) => {
      if (payload === null) {
        return;
      }

      const { sonarrSeriesId: seriesid } = payload;

      const tasks = items
        .filter((v) => v.payload.instance !== undefined)
        .map((v) => {
          const { hi, forced, payload, language } = v;
          const { code2 } = language!;
          const { sonarrEpisodeId: episodeid } = payload.instance!;

          const form: FormType.UploadSubtitle = {
            file: v.file,
            language: code2,
            hi: hi,
            forced: forced,
          };

          return createTask(
            v.file.name,
            episodeid,
            api.episodes.uploadSubtitles,
            seriesid,
            episodeid,
            form
          );
        });

      dispatchTask(TaskGroupName, tasks, "Uploading subtitles...");
    },
    [payload]
  );

  const columns = useMemo<Column<PendingSubtitle<Payload>>[]>(
    () => [
      {
        id: "instance",
        Header: "Episode",
        accessor: "payload",
        className: "vw-1",
        Cell: ({ value, row, update }) => {
          const options = episodes.map<SelectorOption<Item.Episode>>((ep) => ({
            label: `(${ep.season}x${ep.episode}) ${ep.title}`,
            value: ep,
          }));

          const change = useCallback(
            (ep: Nullable<Item.Episode>) => {
              if (ep) {
                const newInfo = { ...row.original };
                newInfo.payload.instance = ep;
                update && update(row, newInfo);
              }
            },
            [row, update]
          );

          return (
            <Selector
              disabled={row.original.state === "fetching"}
              options={options}
              value={value.instance}
              onChange={change}
            ></Selector>
          );
        },
      },
    ],
    [episodes]
  );

  return (
    <SubtitleUploadModal
      columns={columns}
      initial={{ instance: null }}
      availableLanguages={availableLanguages}
      upload={upload}
      update={update}
      validate={validate}
      {...modal}
    ></SubtitleUploadModal>
  );
};

export default SeriesUploadModal;
