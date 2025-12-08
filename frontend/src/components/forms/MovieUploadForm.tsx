import React, { FunctionComponent, useEffect, useMemo } from "react";
import {
  Button,
  Divider,
  MantineColor,
  Select,
  Stack,
  Text,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import {
  faCheck,
  faCircleNotch,
  faInfoCircle,
  faTimes,
  faTrash,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { ColumnDef } from "@tanstack/react-table";
import { isString, uniqBy } from "lodash";
import { useMovieSubtitleModification } from "@/apis/hooks";
import { subtitlesTypeOptions } from "@/components/forms/uploadFormSelectorTypes";
import { Action, Selector } from "@/components/inputs";
import SimpleTable from "@/components/tables/SimpleTable";
import TextPopover from "@/components/TextPopover";
import { useModals, withModal } from "@/modules/modals";
import { useArrayAction, useSelectorOptions } from "@/utilities";
import FormUtils from "@/utilities/form";
import {
  useLanguageProfileBy,
  useProfileItemsToLanguages,
} from "@/utilities/languages";

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
  file: SubtitleFile,
): SubtitleValidateResult => {
  if (file.language === null) {
    return {
      state: "error",
      messages: "Language is not selected",
    };
  } else {
    const { subtitles } = movie;
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
    uniqBy(languages, "code2"),
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
        }))
        .map<SubtitleFile>((v) => ({
          ...v,
          validateResult: validator(movie, v),
        })),
    },
    validate: {
      files: FormUtils.validation((values: SubtitleFile[]) => {
        return (
          values.find(
            (v: SubtitleFile) =>
              v.language === null ||
              v.validateResult === undefined ||
              v.validateResult.state === "error",
          ) === undefined
        );
      }, "Some files cannot be uploaded, please check"),
    },
  });

  useEffect(() => {
    if (form.values.files.length <= 0) {
      modals.closeSelf();
    }
  }, [form.values.files.length, modals]);

  const action = useArrayAction<SubtitleFile>((fn) => {
    form.setValues((values) => {
      const newFiles = fn(values.files ?? []);
      newFiles.forEach((v) => {
        v.validateResult = validator(movie, v);
      });

      return { ...values, files: newFiles };
    });
  });

  const ValidateResultCell = ({
    validateResult,
  }: {
    validateResult: SubtitleValidateResult | undefined;
  }) => {
    const icon = useMemo(() => {
      switch (validateResult?.state) {
        case "valid":
          return faCheck;
        case "warning":
          return faInfoCircle;
        case "error":
          return faTimes;
        default:
          return faCircleNotch;
      }
    }, [validateResult?.state]);

    const color = useMemo<MantineColor | undefined>(() => {
      switch (validateResult?.state) {
        case "valid":
          return "green";
        case "warning":
          return "yellow";
        case "error":
          return "red";
        default:
          return undefined;
      }
    }, [validateResult?.state]);

    return (
      <TextPopover text={validateResult?.messages}>
        <Text c={color} inline>
          <FontAwesomeIcon icon={icon} />
        </Text>
      </TextPopover>
    );
  };

  const columns = useMemo<ColumnDef<SubtitleFile>[]>(
    () => [
      {
        id: "validateResult",
        cell: ({
          row: {
            original: { validateResult },
          },
        }) => {
          return <ValidateResultCell validateResult={validateResult} />;
        },
      },
      {
        header: "File",
        id: "filename",
        accessorKey: "file",
        cell: ({
          row: {
            original: { file },
          },
        }) => {
          return <Text className="table-primary">{file.name}</Text>;
        },
      },
      {
        header: "Language",
        accessorKey: "language",
        cell: ({ row: { original, index } }) => {
          return (
            <Selector
              {...languageOptions}
              className="table-long-break"
              value={original.language}
              onChange={(item) => {
                action.mutate(index, { ...original, language: item });
              }}
            ></Selector>
          );
        },
      },
      {
        header: () => (
          <Selector
            options={subtitlesTypeOptions}
            value={null}
            placeholder="Type"
            onChange={(value) => {
              if (value) {
                action.update((item) => {
                  switch (value) {
                    case "hi":
                      return { ...item, hi: true, forced: false };
                    case "forced":
                      return { ...item, hi: false, forced: true };
                    case "normal":
                      return { ...item, hi: false, forced: false };
                    default:
                      return item;
                  }
                });
              }
            }}
          ></Selector>
        ),
        accessorKey: "type",
        cell: ({ row: { original, index } }) => {
          return (
            <Select
              value={
                subtitlesTypeOptions.find((s) => {
                  if (original.hi) {
                    return s.value === "hi";
                  }

                  if (original.forced) {
                    return s.value === "forced";
                  }

                  return s.value === "normal";
                })?.value
              }
              data={subtitlesTypeOptions}
              onChange={(value) => {
                if (value) {
                  action.mutate(index, {
                    ...original,
                    hi: value === "hi",
                    forced: value === "forced",
                  });
                }
              }}
            ></Select>
          );
        },
      },
      {
        id: "action",
        cell: ({ row: { index } }) => {
          return (
            <Action
              label="Remove"
              icon={faTrash}
              c="red"
              onClick={() => action.remove(index)}
            ></Action>
          );
        },
      },
    ],
    [action, languageOptions],
  );

  const { upload } = useMovieSubtitleModification();

  return (
    <form
      onSubmit={form.onSubmit(({ files }) => {
        const { radarrId } = movie;

        files.forEach(async ({ file, language, hi, forced }) => {
          if (language === null) {
            throw new Error("Language is not selected");
          }

          await upload.mutateAsync({
            radarrId,
            form: { file, language: language.code2, hi, forced },
          });
        });

        onComplete?.();
        modals.closeSelf();
      })}
    >
      <Stack className="table-long-break">
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
  },
);

export default MovieUploadForm;
