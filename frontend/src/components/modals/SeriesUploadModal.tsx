import {
  useEpisodesBySeriesId,
  useEpisodeSubtitleModification,
} from "@/apis/hooks";
import api from "@/apis/raw";
import { withModal } from "@/modules/modals";
import { createTask, dispatchTask } from "@/modules/task/utilities";
import { useSelectorOptions } from "@/utilities";
import {
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "@/utilities/languages";
import { FunctionComponent, useCallback, useMemo } from "react";
import { Column } from "react-table";
import { Selector } from "../inputs";
import SubtitleUploader, {
  PendingSubtitle,
  useRowMutation,
  Validator,
} from "./SubtitleUploadModal";

interface Payload {
  instance: Item.Episode | null;
}

interface Props {
  payload: Item.Series;
}

const SeriesUploadModal: FunctionComponent<Props> = ({ payload }) => {
  const { data: episodes = [] } = useEpisodesBySeriesId(payload.sonarrSeriesId);
  const profile = useLanguageProfileBy(payload?.profileId);

  const availableLanguages = useProfileItemsToLanguages(profile);

  const {
    upload: { mutateAsync },
  } = useEpisodeSubtitleModification();

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

      const { sonarrSeriesId: seriesId } = payload;

      const tasks = items
        .filter((v) => v.payload.instance !== undefined)
        .map((v) => {
          const {
            hi,
            forced,
            payload: { instance },
            language,
          } = v;

          if (language === null || instance === null) {
            throw new Error("Invalid state");
          }

          const { code2 } = language;
          const { sonarrEpisodeId: episodeId } = instance;

          const form: FormType.UploadSubtitle = {
            file: v.file,
            language: code2,
            hi: hi,
            forced: forced,
          };

          return createTask(v.file.name, mutateAsync, {
            seriesId,
            episodeId,
            form,
          });
        });

      dispatchTask(tasks, "upload-subtitles");
    },
    [mutateAsync, payload]
  );

  const columns = useMemo<Column<PendingSubtitle<Payload>>[]>(
    () => [
      {
        id: "instance",
        Header: "Episode",
        accessor: "payload",
        Cell: ({ value, row }) => {
          const options = useSelectorOptions(
            episodes,
            (ep) => `(${ep.season}x${ep.episode}) ${ep.title}`
          );

          const mutate = useRowMutation();

          return (
            <Selector
              {...options}
              disabled={row.original.state === "fetching"}
              value={value.instance}
              onChange={(ep: Nullable<Item.Episode>) => {
                if (ep) {
                  const newInfo = { ...row.original };
                  newInfo.payload.instance = ep;
                  mutate(row.index, newInfo);
                }
              }}
            ></Selector>
          );
        },
      },
    ],
    [episodes]
  );

  return (
    <SubtitleUploader
      columns={columns}
      initial={{ instance: null }}
      availableLanguages={availableLanguages}
      upload={upload}
      update={update}
      validate={validate}
    ></SubtitleUploader>
  );
};

export default withModal(SeriesUploadModal, "series-upload", { size: "xl" });
