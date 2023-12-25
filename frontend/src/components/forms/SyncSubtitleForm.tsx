/* eslint-disable camelcase */

import { useRefTracksById, useSubtitleAction } from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import { syncMaxOffsetSecondsOptions } from "@/pages/Settings/Subtitles/options";
import { toPython } from "@/utilities";
import { faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { Alert, Button, Checkbox, Divider, Stack, Text } from "@mantine/core";
import { useForm } from "@mantine/form";
import { FunctionComponent } from "react";
import { Selector, SelectorOption } from "../inputs";

const TaskName = "Syncing Subtitle";

function useReferencedSubtitles(
  mediaType: "episode" | "movie",
  mediaId: number,
  subtitlesPath: string
) {
  const mediaData = useRefTracksById(
    subtitlesPath,
    mediaType === "episode" ? mediaId : undefined,
    mediaType === "movie" ? mediaId : undefined
  );

  const subtitles: { group: string; value: string; label: string }[] = [];

  if (!mediaData.data) {
    return [];
  } else {
    if (mediaData.data.audio_tracks.length > 0) {
      mediaData.data.audio_tracks.forEach(function (item) {
        subtitles.push({
          group: "Embedded audio tracks",
          value: item.stream,
          label: `${item.name || item.language} (${item.stream})`,
        });
      });
    }

    if (mediaData.data.embedded_subtitles_tracks.length > 0) {
      mediaData.data.embedded_subtitles_tracks.forEach(function (item) {
        subtitles.push({
          group: "Embedded subtitles tracks",
          value: item.stream,
          label: `${item.name || item.language} (${item.stream})`,
        });
      });
    }

    if (mediaData.data.external_subtitles_tracks.length > 0) {
      mediaData.data.external_subtitles_tracks.forEach(function (item) {
        if (item) {
          subtitles.push({
            group: "External Subtitles files",
            value: item.path,
            label: item.name,
          });
        }
      });
    }

    return subtitles;
  }
}

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

interface FormValues {
  reference?: string;
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
  const subtitlesPath = selections[0].path;

  const subtitles: SelectorOption<string>[] = useReferencedSubtitles(
    mediaType,
    mediaId,
    subtitlesPath
  );

  const form = useForm<FormValues>({
    initialValues: {
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
            reference: parameters.reference,
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
          disabled={subtitles.length === 0 || selections.length !== 1}
          label="Reference"
          placeholder="Default: choose automatically within video file"
          options={subtitles}
          {...form.getInputProps("reference")}
        ></Selector>
        <Selector
          clearable
          label="Max Offset Seconds"
          options={syncMaxOffsetSecondsOptions}
          placeholder="Select..."
          {...form.getInputProps("maxOffsetSeconds")}
        ></Selector>
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
