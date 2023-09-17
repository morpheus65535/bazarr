import { useSubtitleAction } from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { syncMaxOffsetSecondsOptions } from "@/pages/Settings/Subtitles/options";
import { Button, Checkbox, Divider, Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { FunctionComponent } from "react";
import { Selector } from "../inputs";

const TaskName = "Syncing Subtitle";

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

  // const videoPath = selections.length == 1 ? selections[0].

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
        // TODO

        onSubmit?.();
        modals.closeSelf();
      })}
    >
      <Stack>
        <Selector
          clearable
          label="Max Offset Seconds"
          options={syncMaxOffsetSecondsOptions}
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
