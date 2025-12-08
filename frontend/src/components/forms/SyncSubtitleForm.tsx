/* eslint-disable camelcase */
import { FunctionComponent } from "react";
import { Alert, Button, Checkbox, Divider, Stack, Text } from "@mantine/core";
import { useForm } from "@mantine/form";
import { faInfoCircle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  useRefTracksByEpisodeId,
  useRefTracksByMovieId,
  useSubtitleAction,
} from "@/apis/hooks";
import {
  GroupedSelector,
  GroupedSelectorOptions,
  Selector,
} from "@/components/inputs";
import { useModals, withModal } from "@/modules/modals";
import { syncMaxOffsetSecondsOptions } from "@/pages/Settings/Subtitles/options";
import { fromPython, toPython } from "@/utilities";

function useReferencedSubtitles(
  mediaType: "episode" | "movie",
  mediaId: number,
  subtitlesPath: string,
) {
  // We cannot call hooks conditionally, we rely on useQuery "enabled" option to do only the required API call
  const episodeData = useRefTracksByEpisodeId(
    subtitlesPath,
    mediaId,
    mediaType === "episode",
  );
  const movieData = useRefTracksByMovieId(
    subtitlesPath,
    mediaId,
    mediaType === "movie",
  );

  const mediaData = mediaType === "episode" ? episodeData : movieData;

  const subtitles: GroupedSelectorOptions<string>[] = [];

  if (!mediaData.data) {
    return [];
  } else {
    if (mediaData.data.audio_tracks.length > 0) {
      const embeddedAudioGroup: GroupedSelectorOptions<string> = {
        group: "Embedded audio tracks",
        items: [],
      };

      subtitles.push(embeddedAudioGroup);

      mediaData.data.audio_tracks.forEach((item) => {
        embeddedAudioGroup.items.push({
          value: item.stream,
          label: `${item.name || item.language} (${item.stream})`,
        });
      });
    }

    if (mediaData.data.embedded_subtitles_tracks.length > 0) {
      const embeddedSubtitlesTrackGroup: GroupedSelectorOptions<string> = {
        group: "Embedded subtitles tracks",
        items: [],
      };

      subtitles.push(embeddedSubtitlesTrackGroup);

      mediaData.data.embedded_subtitles_tracks.forEach((item) => {
        embeddedSubtitlesTrackGroup.items.push({
          value: item.stream,
          label: `${item.name || item.language} (${item.stream})`,
        });
      });
    }

    if (mediaData.data.external_subtitles_tracks.length > 0) {
      const externalSubtitlesFilesGroup: GroupedSelectorOptions<string> = {
        group: "External Subtitles files",
        items: [],
      };

      subtitles.push(externalSubtitlesFilesGroup);

      mediaData.data.external_subtitles_tracks.forEach((item) => {
        if (item) {
          externalSubtitlesFilesGroup.items.push({
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
  hi?: boolean;
  forced?: boolean;
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

  const subtitle = selections[0];

  const mediaType = subtitle.type;
  const mediaId = subtitle.id;
  const subtitlesPath = subtitle.path;

  const subtitles = useReferencedSubtitles(mediaType, mediaId, subtitlesPath);

  const form = useForm<FormValues>({
    initialValues: {
      noFixFramerate: false,
      gss: false,
      hi: fromPython(subtitle.hi),
      forced: fromPython(subtitle.forced),
    },
  });

  return (
    <form
      onSubmit={form.onSubmit((parameters) => {
        selections.forEach(async (s) => {
          const form: FormType.ModifySubtitle = {
            ...s,
            reference: parameters.reference,
            max_offset_seconds: parameters.maxOffsetSeconds,
            no_fix_framerate: toPython(parameters.noFixFramerate),
            gss: toPython(parameters.gss),
          };

          await mutateAsync({ action: "sync", form });
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
        <GroupedSelector
          clearable
          disabled={subtitles.length === 0 || selections.length !== 1}
          label="Reference"
          placeholder="Default: choose automatically within video file"
          options={subtitles}
          {...form.getInputProps("reference")}
        ></GroupedSelector>
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
