import { useMovieSubtitleModification } from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { task, TaskGroup } from "@/modules/task";
import { useTableStyles } from "@/styles";
import { useArrayAction, useSelectorOptions } from "@/utilities";
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
import { Button, Checkbox, Divider, Stack, Text } from "@mantine/core";
import { useForm } from "@mantine/hooks";
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
  validateResult?: SubtitleValidateResult;
};

type SubtitleValidateResult = {
  state: "valid" | "warning" | "error";
  messages?: string;
};

const validator = (
  movie: Item.Movie,
  file: SubtitleFile
): SubtitleValidateResult => {
  if (file.language === null) {
    return {
      state: "error",
      messages: "Language is not selected",
    };
  } else {
    const { subtitles } = movie;
    const existing = subtitles.find(
      (v) => v.code2 === file.language?.code2 && isString(v.path)
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
  movie: Item.Movie;
  onComplete?: () => void;
}

const MovieUploadForm: FunctionComponent<Props> = ({
  files,
  movie,
  onComplete,
}) => {
  const modals = useModals();

  const profile = useLanguageProfileBy(movie.profileId);

  const languages = useProfileItemsToLanguages(profile);
  const languageOptions = useSelectorOptions(
    languages,
    (v) => v.name,
    (v) => v.code2
  );

  const defaultLanguage = useMemo(
    () => (languages.length > 0 ? languages[0] : null),
    [languages]
  );

  const form = useForm({
    initialValues: {
      files: files
        .map<SubtitleFile>((file) => ({
          file,
          language: defaultLanguage,
          forced: defaultLanguage?.forced ?? false,
          hi: defaultLanguage?.hi ?? false,
        }))
        .map<SubtitleFile>((v) => ({
          ...v,
          validateResult: validator(movie, v),
        })),
    },
    validationRules: {
      files: (values) => {
        return (
          values.find(
            (v) =>
              v.language === null ||
              v.validateResult === undefined ||
              v.validateResult.state === "error"
          ) === undefined
        );
      },
    },
  });

  useEffect(() => {
    if (form.values.files.length <= 0) {
      modals.closeSelf();
    }
  }, [form.values.files.length, modals]);

  const action = useArrayAction<SubtitleFile>((fn) => {
    form.setValues(({ files, ...rest }) => {
      const newFiles = fn(files);
      newFiles.forEach((v) => {
        v.validateResult = validator(movie, v);
      });
      return { ...rest, files: newFiles };
    });
  });

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

          return (
            <TextPopover text={value?.messages}>
              {/* TODO: Color */}
              <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
            </TextPopover>
          );
        },
      },
      {
        Header: "File",
        id: "filename",
        accessor: "file",
        Cell: ({ value }) => {
          const { classes } = useTableStyles();

          return <Text className={classes.primary}>{value.name}</Text>;
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
                action.mutate(index, { ...original, forced: checked });
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
                action.mutate(index, { ...original, hi: checked });
              }}
            ></Checkbox>
          );
        },
      },
      {
        Header: "Language",
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
        id: "action",
        accessor: "file",
        Cell: ({ row: { index } }) => {
          return (
            <Action
              icon={faTrash}
              color="red"
              onClick={() => action.remove(index)}
            ></Action>
          );
        },
      },
    ],
    [action, languageOptions]
  );

  const { upload } = useMovieSubtitleModification();

  return (
    <form
      onSubmit={form.onSubmit(({ files }) => {
        const { radarrId } = movie;

        files.forEach(({ file, language, hi, forced }) => {
          if (language === null) {
            throw new Error("Language is not selected");
          }

          task.create(file.name, TaskGroup.UploadSubtitle, upload.mutateAsync, {
            radarrId,
            form: { file, language: language.code2, hi, forced },
          });
        });

        onComplete?.();
        modals.closeSelf();
      })}
    >
      <Stack>
        <SimpleTable columns={columns} data={form.values.files}></SimpleTable>
        <Divider></Divider>
        <Button type="submit">Upload</Button>
      </Stack>
    </form>
  );
};

export const MovieUploadModal = withModal(
  MovieUploadForm,
  "upload-movie-subtitle",
  {
    title: "Upload Subtitles",
    size: "xl",
  }
);

export default MovieUploadForm;
