/* eslint-disable camelcase */

import {
  useEpisodesByIds,
  useMovieById,
  useSubtitleAction,
} from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import { syncMaxOffsetSecondsOptions } from "@/pages/Settings/Subtitles/options";
import { toPython, useSelectorOptions } from "@/utilities";
import { faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Alert, Button, Checkbox, Divider, Stack, Text } from "@mantine/core";
import { useForm } from "@mantine/form";
import { isString } from "lodash";
import { FunctionComponent } from "react";
import { Selector } from "../inputs";

const TaskName = "Syncing Subtitle";

function useReferencedSubtitles(
  mediaType: "episode" | "movie",
  mediaId: number
): string[] {
  // We cannot call hooks conditionally, find a better way to handle this
  const { data: movieData } = useMovieById(mediaId);
  const { data: episodeData } = useEpisodesByIds([mediaId]);

  let subtitles: string[] = [];

  switch (mediaType) {
    case "movie":
      if (movieData) {
        subtitles = movieData.subtitles
          .filter((value) => isString(value.path))
          .map((value) => value.path ?? value.name);

        subtitles.push(movieData.path);
      }
      break;
    case "episode":
      if (episodeData) {
        subtitles = episodeData
          .flatMap((episode) => episode.subtitles)
          .filter((value) => isString(value.path))
          .map((value) => value.path ?? value.name);

        subtitles.push(...episodeData.map((value) => value.path));
      }
      break;
  }

  return subtitles;
}

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

interface FormValues {
  originalFormat: boolean;
  reference?: string;
  referenceStream?: string;
  maxOffsetSeconds?: string;
  noFixFramerate: boolean;
  gss: boolean;
}

const SyncSubtitleForm: FunctionComponent<Props> = ({
  selections,
  onSubmit,
}) => {
  if (selections.length === 0) {
    throw new Error("You need to select at least 1 media to sync");
  }

  const { mutateAsync } = useSubtitleAction();
  const modals = useModals();

  const mediaType = selections[0].type;
  const mediaId = selections[0].id;

  const subtitles = useReferencedSubtitles(mediaType, mediaId);
  const subtitleOptions = useSelectorOptions(subtitles, (value) => value);

  // We only shows the reference stream when user selects subtitles in the same episode or movie
  const disableReferenceSelector =
    selections.some(({ id }) => id !== mediaId) || subtitles.length === 0;

  const form = useForm<FormValues>({
    initialValues: {
      originalFormat: false,
      noFixFramerate: false,
      gss: false,
    },
  });

  return (
    <form
      onSubmit={form.onSubmit((parameters) => {
        selections.forEach((s) => {
          const form: FormType.ModifySubtitle = {
            ...s,
            original_format: toPython(parameters.originalFormat),
            reference: parameters.reference,
            reference_stream: parameters.referenceStream,
            max_offset_seconds: parameters.maxOffsetSeconds,
            no_fix_framerate: toPython(parameters.noFixFramerate),
            gss: toPython(parameters.gss),
          };

          task.create(s.path, TaskName, mutateAsync, { action: "sync", form });
        });

        onSubmit?.();
        modals.closeSelf();
      })}
    >
      <Stack>
        <Alert
          title="Subtitles"
          color="gray"
          icon={<FontAwesomeIcon icon={faInfoCircle}></FontAwesomeIcon>}
        >
          <Text size="sm">{selections.length} subtitles selected</Text>
        </Alert>
        <Selector
          clearable
          disabled={disableReferenceSelector}
          label="Reference"
          placeholder="Select Reference..."
          {...subtitleOptions}
          {...form.getInputProps("reference")}
        ></Selector>
        {/* TODO: Reference Stream */}
        <Selector
          clearable
          label="Max Offset Seconds"
          options={syncMaxOffsetSecondsOptions}
          placeholder="Select..."
          {...form.getInputProps("maxOffsetSeconds")}
        ></Selector>
        <Checkbox
          label="Original Format"
          {...form.getInputProps("originalFormat")}
        ></Checkbox>
        <Checkbox
          label="No Fix Framerate"
          {...form.getInputProps("noFixFramerate")}
        ></Checkbox>
        <Checkbox
          label="Golden-Section Search"
          {...form.getInputProps("gss")}
        ></Checkbox>
        <Divider></Divider>
        <Button type="submit">Sync</Button>
      </Stack>
    </form>
  );
};

export const SyncSubtitleModal = withModal(SyncSubtitleForm, "sync-subtitle", {
  title: "Sync Subtitle Options",
  size: "lg",
});

export default SyncSubtitleForm;
