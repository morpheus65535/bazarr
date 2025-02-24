import { FunctionComponent } from "react";
import { Button, Divider, Group, NumberInput, Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { faMinus, faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useSubtitleAction } from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import FormUtils from "@/utilities/form";

const TaskName = "Changing Time";

function convertToAction(h: number, m: number, s: number, ms: number) {
  return `shift_offset(h=${h},m=${m},s=${s},ms=${ms})`;
}

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

const TimeOffsetForm: FunctionComponent<Props> = ({ selections, onSubmit }) => {
  const { mutateAsync } = useSubtitleAction();
  const modals = useModals();

  const form = useForm({
    initialValues: {
      positive: true,
      hour: 0,
      min: 0,
      sec: 0,
      ms: 0,
    },
    validate: {
      hour: FormUtils.validation(
        (v: number) => v >= 0,
        "Hour must be larger than 0",
      ),
      min: FormUtils.validation(
        (v: number) => v >= 0,
        "Minute must be larger than 0",
      ),
      sec: FormUtils.validation(
        (v: number) => v >= 0,
        "Second must be larger than 0",
      ),
      ms: FormUtils.validation(
        (v: number) => v >= 0,
        "Millisecond must be larger than 0",
      ),
    },
  });

  const enabled =
    form.values.hour > 0 ||
    form.values.min > 0 ||
    form.values.sec > 0 ||
    form.values.ms > 0;

  return (
    <form
      onSubmit={form.onSubmit(({ positive, hour, min, sec, ms }) => {
        let action: string;
        if (positive) {
          action = convertToAction(hour, min, sec, ms);
        } else {
          action = convertToAction(-hour, -min, -sec, -ms);
        }

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
        <Group align="end" gap="xs" wrap="nowrap">
          <Button
            color="gray"
            variant="filled"
            style={{ overflow: "visible" }}
            onClick={() =>
              form.setValues((f) => ({ ...f, positive: !f.positive }))
            }
          >
            <FontAwesomeIcon
              icon={form.values.positive ? faPlus : faMinus}
            ></FontAwesomeIcon>
          </Button>
          <NumberInput
            min={0}
            label="hour"
            {...form.getInputProps("hour")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="min"
            {...form.getInputProps("min")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="sec"
            {...form.getInputProps("sec")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="ms"
            {...form.getInputProps("ms")}
          ></NumberInput>
        </Group>
        <Divider></Divider>
        <Button disabled={!enabled} type="submit">
          Start
        </Button>
      </Stack>
    </form>
  );
};

export const TimeOffsetModal = withModal(TimeOffsetForm, "time-offset", {
  title: "Change Time",
});

export default TimeOffsetForm;
