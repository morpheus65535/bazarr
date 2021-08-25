import React, { FunctionComponent, useCallback } from "react";
import { dispatchTask } from "../../@modules/task";
import { createTask } from "../../@modules/task/utilities";
import { useProfileBy, useProfileItemsToLanguages } from "../../@redux/hooks";
import { MoviesApi } from "../../apis";
import { BaseModalProps } from "./BaseModal";
import { useModalInformation } from "./hooks";
import SubtitleUploadModal, {
  PendingSubtitle,
  Validator,
} from "./SubtitleUploadModal";

interface Payload {}

export const TaskGroupName = "Uploading Subtitles...";

const MovieUploadModal: FunctionComponent<BaseModalProps> = (props) => {
  const modal = props;

  const { payload } = useModalInformation<Item.Movie>(modal.modalKey);

  const profile = useProfileBy(payload?.profileId);

  const availableLanguages = useProfileItemsToLanguages(profile);

  const update = useCallback(async (list: PendingSubtitle<Payload>[]) => {
    return list;
  }, []);

  const validate = useCallback<Validator<Payload>>(
    (item) => {
      if (item.language === null) {
        return {
          state: "error",
          messages: ["Language is not selected"],
        };
      } else if (
        payload?.subtitles.find((v) => v.code2 === item.language?.code2) !==
        undefined
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
    },
    [payload?.subtitles]
  );

  const upload = useCallback(
    (items: PendingSubtitle<Payload>[]) => {
      if (payload === null) {
        return;
      }

      const { radarrId } = payload;

      const tasks = items
        .filter((v) => v.language !== null)
        .map((v) => {
          const { file, language, forced, hi } = v;

          return createTask(
            file.name,
            radarrId,
            MoviesApi.uploadSubtitles.bind(MoviesApi),
            radarrId,
            {
              file,
              forced,
              hi,
              language: language!.code2,
            }
          );
        });

      dispatchTask(TaskGroupName, tasks, "Uploading...");
    },
    [payload]
  );

  return (
    <SubtitleUploadModal
      hideAllLanguages
      initial={{ forced: false }}
      availableLanguages={availableLanguages}
      columns={[]}
      upload={upload}
      update={update}
      validate={validate}
      {...modal}
    ></SubtitleUploadModal>
  );
};

export default MovieUploadModal;
