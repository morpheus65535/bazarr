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
import { isString, uniqBy } from "lodash";
import {
  useSportsEventsByLeagueId,
  useSportsSubtitleModification,
  useSubtitleInfos,
} from "@/apis/hooks";
import { subtitlesTypeOptions } from "@/components/forms/uploadFormSelectorTypes";
import { Action, Selector } from "@/components/inputs";
import { AppColumnDef as ColumnDef } from "@/components/tables/features";
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
  event: Item.SportsEvent | null;
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
  } else if (file.event === null) {
    return {
      state: "error",
      messages: "Event is not selected",
    };
  } else {
    const { subtitles } = file.event;
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
  league: Item.SportsLeague;
  onComplete?: VoidFunction;
}

const SportsUploadForm: FunctionComponent<Props> = ({
  league,
  files,
  onComplete,
}) => {
  const modals = useModals();
  const events = useSportsEventsByLeagueId(league.sportarrLeagueId);
  const eventOptions = useSelectorOptions(
    events.data ?? [],
    (v) =>
      `(${v.season}x${v.episode}) ${v.partName ? `${v.title} - ${v.partName}` : v.title}`,
    (v) => v.sportsEventId.toString(),
  );

  const profile = useLanguageProfileBy(league.profileId);
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
          event: null,
        }))
        .map<SubtitleFile>((file) => ({
          ...file,
          validateResult: validator(file),
        })),
    },
    validate: {
      files: FormUtils.validation(
        (values: SubtitleFile[]) =>
          values.find(
            (v: SubtitleFile) =>
              v.language === null ||
              v.event === null ||
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

  // Auto assign event if available
  useEffect(() => {
    if (infos.data !== undefined) {
      action.update((item) => {
        const info = infos.data.find((v) => v.filename === item.file.name);
        if (info) {
          const matches =
            events.data?.filter(
              (v) => v.season === info.season && v.episode === info.episode,
            ) ?? [];
          // The parts of a multi part event share a season and an episode.
          // Only assign when the match is not ambiguous.
          if (matches.length === 1) {
            item.event = matches[0];
          }
        }
        return item;
      });
    }
  }, [action, events.data, infos.data]);

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
          return "success";
        case "warning":
          return "warning";
        case "error":
          return "danger";
        default:
          return undefined;
      }
    }, [validateResult?.state]);

    return (
      <TextPopover text={validateResult?.messages}>
        <Text c={color} inline>
          <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
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
            original: {
              file: { name },
            },
          },
        }) => {
          return <Text className="table-primary">{name}</Text>;
        },
      },
      {
        header: () => (
          <Selector
            {...languageOptions}
            value={null}
            placeholder="Language"
            onChange={(value) => {
              if (value) {
                action.update((item) => {
                  return { ...item, language: value };
                });
              }
            }}
          ></Selector>
        ),
        accessorKey: "language",
        cell: ({ row: { original, index } }) => {
          return (
            <Selector
              {...languageOptions}
              className="table-select"
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
        id: "event",
        header: "Event",
        accessorKey: "event",
        cell: ({ row: { original, index } }) => {
          return (
            <Selector
              {...eventOptions}
              searchable
              className="table-select"
              value={original.event}
              onChange={(item) => {
                action.mutate(index, { ...original, event: item });
              }}
            ></Selector>
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
              c="danger"
              onClick={() => action.remove(index)}
            ></Action>
          );
        },
      },
    ],
    [action, eventOptions, languageOptions],
  );

  const { upload } = useSportsSubtitleModification();

  return (
    <form
      onSubmit={form.onSubmit(({ files }) => {
        const { sportarrLeagueId: leagueId } = league;

        for (const value of files) {
          const { file, hi, forced, language, event } = value;

          if (language === null || event === null) {
            throw new Error(
              "Invalid language or event. This shouldn't happen, please report this bug.",
            );
          }

          const { code2 } = language;
          const { sportsEventId: eventId } = event;

          upload.mutate({
            leagueId,
            eventId,
            form: {
              file,
              language: code2,
              hi,
              forced,
            },
          });
        }

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

export const SportsUploadModal = withModal(
  SportsUploadForm,
  "upload-sports-subtitles",
  { title: "Upload Subtitles", size: "xl" },
);

export default SportsUploadForm;
