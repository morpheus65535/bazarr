import { useModals, withModal } from "@/modules/modals";
import { useArrayAction, useSelectorOptions } from "@/utilities";
import { useProfileItemsToLanguages } from "@/utilities/languages";
import { faXmark } from "@fortawesome/free-solid-svg-icons";
import { Button, Checkbox, Divider, Stack } from "@mantine/core";
import { useForm } from "@mantine/hooks";
import { FunctionComponent, useMemo } from "react";
import { Column } from "react-table";
import { Action, Selector } from "../inputs";
import { SimpleTable } from "../tables";

type SubtitleFile = {
  file: File;
  language: Language.Info | null;
  forced: boolean;
  hi: boolean;
  validateResult?: SubtitleValidateResult;
};

type SubtitleValidateResult = {
  filename: string;
  state: "valid" | "warning" | "error";
  messages: string[];
};

interface Props {
  files: File[];
  profile: Language.Profile;
  onComplete: (files: SubtitleFile[]) => void;
}

const SubtitleUploadForm: FunctionComponent<Props> = ({
  files,
  profile,
  onComplete,
}) => {
  const modals = useModals();

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
    initialValues: files.map<SubtitleFile>((file) => ({
      file,
      language: defaultLanguage,
      forced: defaultLanguage?.forced ?? false,
      hi: defaultLanguage?.hi ?? false,
    })),
  });

  const action = useArrayAction(form.setValues);

  const columns = useMemo<Column<SubtitleFile>[]>(
    () => [
      {
        id: "action",
        accessor: "file",
        Cell: ({ row: { index } }) => {
          return (
            <Action
              icon={faXmark}
              onClick={() => action.remove(index)}
            ></Action>
          );
        },
      },
      {
        Header: "File",
        accessor: (d) => d.file.name,
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
        Header: () => (
          <Selector
            {...languageOptions}
            placeholder="Language"
            value={null}
            onChange={(value) => {
              action.update((v) => {
                v.language = value;
                return v;
              });
            }}
          ></Selector>
        ),
        accessor: "language",
        Cell: ({ row: { original, index }, value }) => {
          return (
            <Selector
              {...languageOptions}
              value={value}
              onChange={(item) => {
                action.mutate(index, { ...original, language: item });
              }}
            ></Selector>
          );
        },
      },
    ],
    [action, languageOptions]
  );

  return (
    <form
      onSubmit={form.onSubmit((files) => {
        onComplete(files);
        modals.closeSelf();
      })}
    >
      <Stack>
        <SimpleTable columns={columns} data={form.values}></SimpleTable>
        <Divider></Divider>
        <Button type="submit">Upload</Button>
      </Stack>
    </form>
  );
};

export const SubtitleUploadModal = withModal(
  SubtitleUploadForm,
  "subtitle-uploader",
  {
    title: "Upload Subtitles",
    size: "xl",
  }
);

export default SubtitleUploadForm;
