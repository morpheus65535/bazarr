import { FunctionComponent } from "react";
import { Button, Divider, Group, NumberInput, Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useSubtitleAction } from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import FormUtils from "@/utilities/form";

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
      from: FormUtils.validation(
        (value: number) => value > 0,
        "The From value must be larger than 0",
      ),
      to: FormUtils.validation(
        (value: number) => value > 0,
        "The To value must be larger than 0",
      ),
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
          }),
        );

        onSubmit?.();
        modals.closeSelf();
      })}
    >
      <Stack>
        <Group gap="xs" grow>
          <NumberInput
            placeholder="From"
            decimalScale={2}
            fixedDecimalScale
            {...form.getInputProps("from")}
          ></NumberInput>
          <NumberInput
            placeholder="To"
            decimalScale={2}
            fixedDecimalScale
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
