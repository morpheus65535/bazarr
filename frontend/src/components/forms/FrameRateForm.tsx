import { useSubtitleAction } from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import { Button, Divider, Group, NumberInput, Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { FunctionComponent } from "react";

const TaskName = "Changing Frame Rate";

function convertToAction(from: number, to: number) {
  return `change_FPS(from=${from},to=${to})`;
}

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

const FrameRateForm: FunctionComponent<Props> = ({ selections, onSubmit }) => {
  const { mutateAsync } = useSubtitleAction();
  const modals = useModals();

  const form = useForm({
    initialValues: {
      from: 0,
      to: 0,
    },
    validate: {
      from: (v) => v > 0,
      to: (v) => v > 0,
    },
  });

  return (
    <form
      onSubmit={form.onSubmit(({ from, to }) => {
        const action = convertToAction(from, to);

        selections.forEach((s) =>
          task.create(s.path, TaskName, mutateAsync, {
            action,
            form: s,
          })
        );

        onSubmit?.();
        modals.closeSelf();
      })}
    >
      <Stack>
        <Group spacing="xs" grow>
          <NumberInput
            placeholder="From"
            {...form.getInputProps("from")}
          ></NumberInput>
          <NumberInput
            placeholder="To"
            {...form.getInputProps("to")}
          ></NumberInput>
        </Group>
        <Divider></Divider>
        <Button type="submit">Start</Button>
      </Stack>
    </form>
  );
};

export const FrameRateModal = withModal(FrameRateForm, "frame-rate-tool", {
  title: "Change Frame Rate",
});

export default FrameRateForm;
