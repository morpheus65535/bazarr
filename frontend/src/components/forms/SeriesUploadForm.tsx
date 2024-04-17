import {
  useEpisodesBySeriesId,
  useEpisodeSubtitleModification,
  useSubtitleInfos,
} from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { task, TaskGroup } from "@/modules/task";
import { useTableStyles } from "@/styles";
import { useArrayAction, useSelectorOptions } from "@/utilities";
import FormUtils from "@/utilities/form";
import {
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "@/utilities/languages";
import {
  faCheck,
  faCircleNotch,
  faInfoCircle,
  faTimes,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  Button,
  Checkbox,
  createStyles,
  Divider,
  MantineColor,
  Stack,
  Text,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { isString } from "lodash";
import { FunctionComponent, useEffect, useMemo } from "react";
import { Column } from "react-table";
import { Action, Selector } from "../inputs";
import { SimpleTable } from "../tables";
import TextPopover from "../TextPopover";

type SubtitleFile = {
  file: File;
  language: Language.Info | null;
  forced: boolean;
  hi: boolean;
  episode: Item.Episode | null;
  validateResult?: SubtitleValidateResult;
};

type SubtitleValidateResult = {
  state: "valid" | "warning" | "error";
  messages?: string;
};

const validator = (file: SubtitleFile): SubtitleValidateResult => {
  if (file.language === null) {
    return {
      state: "error",
      messages: "Language is not selected",
    };
  } else if (file.episode === null) {
    return {
      state: "error",
      messages: "Episode is not selected",
    };
  } else {
    const { subtitles } = file.episode;
    const existing = subtitles.find(
      (v) => v.code2 === file.language?.code2 && isString(v.path),
    );
    if (existing !== undefined) {
      return {
        state: "warning",
        messages: "Override existing subtitle",
      };
    }
  }

  return {
    state: "valid",
  };
};

interface Props {
  files: File[];
  series: Item.Series;
  onComplete?: VoidFunction;
}

const useStyles = createStyles((theme) => {
  return {
    wrapper: {
      overflowWrap: "anywhere",
    },
  };
});

const SeriesUploadForm: FunctionComponent<Props> = ({
  series,
  files,
  onComplete,
}) => {
  const modals = useModals();
  const { classes } = useStyles();
  const episodes = useEpisodesBySeriesId(series.sonarrSeriesId);
  const episodeOptions = useSelectorOptions(
    episodes.data ?? [],
    (v) => `(${v.season}x${v.episode}) ${v.title}`,
    (v) => v.sonarrEpisodeId.toString(),
  );

  const profile = useLanguageProfileBy(series.profileId);
  const languages = useProfileItemsToLanguages(profile);
  const languageOptions = useSelectorOptions(
    languages,
    (v) => v.name,
    (v) => v.code2,
  );

  const defaultLanguage = useMemo(
    () => (languages.length > 0 ? languages[0] : null),
    [languages],
  );

  const form = useForm({
    initialValues: {
      files: files
        .map<SubtitleFile>((file) => ({
          file,
          language: defaultLanguage,
          forced: defaultLanguage?.forced ?? false,
          hi: defaultLanguage?.hi ?? false,
          episode: null,
        }))
        .map<SubtitleFile>((file) => ({
          ...file,
          validateResult: validator(file),
        })),
    },
    validate: {
      files: FormUtils.validation(
        (values) =>
          values.find(
            (v) =>
              v.language === null ||
              v.episode === null ||
              v.validateResult === undefined ||
              v.validateResult.state === "error",
          ) === undefined,
        "Some files cannot be uploaded, please check",
      ),
    },
  });

  const action = useArrayAction<SubtitleFile>((fn) => {
    form.setValues((values) => {
      const newFiles = fn(values.files ?? []);
      newFiles.forEach((v) => {
        v.validateResult = validator(v);
      });
      return { ...values, files: newFiles };
    });
  });

  const names = useMemo(() => files.map((v) => v.name), [files]);
  const infos = useSubtitleInfos(names);

  // Auto assign episode if available
  useEffect(() => {
    if (infos.data !== undefined) {
      action.update((item) => {
        const info = infos.data.find((v) => v.filename === item.file.name);
        if (info) {
          item.episode =
            episodes.data?.find(
              (v) => v.season === info.season && v.episode === info.episode,
            ) ?? item.episode;
        }
        return item;
      });
    }
  }, [action, episodes.data, infos.data]);

  const columns = useMemo<Column<SubtitleFile>[]>(
    () => [
      {
        accessor: "validateResult",
        Cell: ({ cell: { value } }) => {
          const icon = useMemo(() => {
            switch (value?.state) {
              case "valid":
                return faCheck;
              case "warning":
                return faInfoCircle;
              case "error":
                return faTimes;
              default:
                return faCircleNotch;
            }
          }, [value?.state]);

          const color = useMemo<MantineColor | undefined>(() => {
            switch (value?.state) {
              case "valid":
                return "green";
              case "warning":
                return "yellow";
              case "error":
                return "red";
              default:
                return undefined;
            }
          }, [value?.state]);

          return (
            <TextPopover text={value?.messages}>
              <Text color={color} inline>
                <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
              </Text>
            </TextPopover>
          );
        },
      },
      {
        Header: "File",
        id: "filename",
        accessor: "file",
        Cell: ({ value: { name } }) => {
          const { classes } = useTableStyles();
          return <Text className={classes.primary}>{name}</Text>;
        },
      },
      {
        Header: "Forced",
        accessor: "forced",
        Cell: ({ row: { original, index }, value }) => {
          return (
            <Checkbox
              checked={value}
              onChange={({ currentTarget: { checked } }) => {
                action.mutate(index, {
                  ...original,
                  forced: checked,
                  hi: checked ? false : original.hi,
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        Header: "HI",
        accessor: "hi",
        Cell: ({ row: { original, index }, value }) => {
          return (
            <Checkbox
              checked={value}
              onChange={({ currentTarget: { checked } }) => {
                action.mutate(index, {
                  ...original,
                  hi: checked,
                  forced: checked ? false : original.forced,
                });
              }}
            ></Checkbox>
          );
        },
      },
      {
        Header: (
          <Selector
            {...languageOptions}
            value={null}
            placeholder="Language"
            onChange={(value) => {
              if (value) {
                action.update((item) => {
                  item.language = value;
                  return item;
                });
              }
            }}
          ></Selector>
        ),
        accessor: "language",
        Cell: ({ row: { original, index }, value }) => {
          const { classes } = useTableStyles();
          return (
            <Selector
              {...languageOptions}
              className={classes.select}
              value={value}
              onChange={(item) => {
                action.mutate(index, { ...original, language: item });
              }}
            ></Selector>
          );
        },
      },
      {
        id: "episode",
        Header: "Episode",
        accessor: "episode",
        Cell: ({ value, row }) => {
          const { classes } = useTableStyles();
          return (
            <Selector
              {...episodeOptions}
              searchable
              className={classes.select}
              value={value}
              onChange={(item) => {
                action.mutate(row.index, { ...row.original, episode: item });
              }}
            ></Selector>
          );
        },
      },
      {
        id: "action",
        accessor: "file",
        Cell: ({ row: { index } }) => {
          return (
            <Action
              label="Remove"
              icon={faTrash}
              color="red"
              onClick={() => action.remove(index)}
            ></Action>
          );
        },
      },
    ],
    [action, episodeOptions, languageOptions],
  );

  const { upload } = useEpisodeSubtitleModification();

  return (
    <form
      onSubmit={form.onSubmit(({ files }) => {
        const { sonarrSeriesId: seriesId } = series;

        files.forEach((value) => {
          const { file, hi, forced, language, episode } = value;

          if (language === null || episode === null) {
            throw new Error(
              "Invalid language or episode. This shouldn't happen, please report this bug.",
            );
          }

          const { code2 } = language;
          const { sonarrEpisodeId: episodeId } = episode;

          task.create(file.name, TaskGroup.UploadSubtitle, upload.mutateAsync, {
            seriesId,
            episodeId,
            form: {
              file,
              language: code2,
              hi,
              forced,
            },
          });
        });

        onComplete?.();
        modals.closeSelf();
      })}
    >
      <Stack className={classes.wrapper}>
        <SimpleTable columns={columns} data={form.values.files}></SimpleTable>
        <Divider></Divider>
        <Button type="submit">Upload</Button>
      </Stack>
    </form>
  );
};

export const SeriesUploadModal = withModal(
  SeriesUploadForm,
  "upload-series-subtitles",
  { title: "Upload Subtitles", size: "xl" },
);

export default SeriesUploadForm;
