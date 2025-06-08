import { FunctionComponent } from "react";
import {
  Button,
  Divider,
  Group,
  InputLabel,
  NumberInput,
  Stack,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useSubtitleAction } from "@/apis/hooks";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import FormUtils from "@/utilities/form";

const TaskName = "Linearly Aligning";

function convertToAction(
  h: number,
  m: number,
  s: number,
  ms: number,
  scale: number,
) {
  return `linear_align(h=${h},m=${m},s=${s},ms=${ms},scale=${scale})`;
}

function convertToMs(h: number, m: number, s: number, ms: number) {
  return h * 3600000 + m * 60000 + s * 1000 + ms;
}

function convertToTime(ms: number) {
  const hours = Math.floor(ms / 3600000);
  ms %= 3600000;
  const minutes = Math.floor(ms / 60000);
  ms %= 60000;
  const seconds = Math.floor(ms / 1000);
  const milliseconds = ms % 1000;
  return { h: hours, m: minutes, s: seconds, ms: milliseconds };
}

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

const LinearAlignForm: FunctionComponent<Props> = ({
  selections,
  onSubmit,
}) => {
  const { mutateAsync } = useSubtitleAction();
  const modals = useModals();

  const timeInput = { hour: 0, min: 0, sec: 0, ms: 0 };
  const alignInput = { from: timeInput, to: timeInput };

  const timeInputValidation = {
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
  };
  const alignInputValidation = {
    from: timeInputValidation,
    to: timeInputValidation,
  };

  const form = useForm({
    initialValues: {
      first: alignInput,
      second: alignInput,
    },
    validate: {
      first: alignInputValidation,
      second: alignInputValidation,
    },
  });

  const enabled =
    form.values.first.from.hour > 0 ||
    form.values.first.from.min > 0 ||
    form.values.first.from.sec > 0 ||
    form.values.first.from.ms > 0 ||
    form.values.first.to.hour > 0 ||
    form.values.first.to.min > 0 ||
    form.values.first.to.sec > 0 ||
    form.values.first.to.ms > 0 ||
    form.values.second.from.hour > 0 ||
    form.values.second.from.min > 0 ||
    form.values.second.from.sec > 0 ||
    form.values.second.from.ms > 0 ||
    form.values.second.from.hour > 0 ||
    form.values.second.from.min > 0 ||
    form.values.second.from.sec > 0 ||
    form.values.second.from.ms > 0 ||
    true;

  return (
    <form
      onSubmit={form.onSubmit(({ first, second }) => {
        const firstActual: number = convertToMs(
          first.from.hour,
          first.from.min,
          first.from.sec,
          first.from.ms,
        );
        const firstSupposed: number = convertToMs(
          first.to.hour,
          first.to.min,
          first.to.sec,
          first.to.ms,
        );
        const firstOffset = firstSupposed;
        const { h, m, s, ms } = convertToTime(firstOffset);

        const secondActual: number = convertToMs(
          second.from.hour,
          second.from.min,
          second.from.sec,
          second.from.ms,
        );
        const secondSupposed: number = convertToMs(
          second.to.hour,
          second.to.min,
          second.to.sec,
          second.to.ms,
        );

        const actualDiff = secondActual - firstActual - firstActual;
        const actualSupposed = secondSupposed - firstSupposed - firstActual;
        const scale: number = actualSupposed / actualDiff;

        const action: string = convertToAction(h, m, s, ms, scale);
        console.log(h, m, s, ms, scale, action);

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
        <InputLabel>(First) time in subtitle</InputLabel>
        <Group align="end" gap="xs" wrap="nowrap">
          <NumberInput
            min={0}
            label="hour"
            {...form.getInputProps("first.from.hour")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="min"
            {...form.getInputProps("first.from.min")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="sec"
            {...form.getInputProps("first.from.sec")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="ms"
            {...form.getInputProps("first.from.ms")}
          ></NumberInput>
        </Group>
        <InputLabel>(First) time in movie</InputLabel>
        <Group align="end" gap="xs" wrap="nowrap">
          <NumberInput
            min={0}
            label="hour"
            {...form.getInputProps("first.to.hour")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="min"
            {...form.getInputProps("first.to.min")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="sec"
            {...form.getInputProps("first.to.sec")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="ms"
            {...form.getInputProps("first.to.ms")}
          ></NumberInput>
        </Group>

        <Divider></Divider>
        <InputLabel>(Second) time in subtitle</InputLabel>
        <Group align="end" gap="xs" wrap="nowrap">
          <NumberInput
            min={0}
            label="hour"
            {...form.getInputProps("second.from.hour")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="min"
            {...form.getInputProps("second.from.min")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="sec"
            {...form.getInputProps("second.from.sec")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="ms"
            {...form.getInputProps("second.from.ms")}
          ></NumberInput>
        </Group>
        <InputLabel>(Second) time in movie</InputLabel>
        <Group align="end" gap="xs" wrap="nowrap">
          <NumberInput
            min={0}
            label="hour"
            {...form.getInputProps("second.to.hour")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="min"
            {...form.getInputProps("second.to.min")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="sec"
            {...form.getInputProps("second.to.sec")}
          ></NumberInput>
          <NumberInput
            min={0}
            label="ms"
            {...form.getInputProps("second.to.ms")}
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

export const LinearAlignModal = withModal(LinearAlignForm, "linear-align", {
  title: "Linear Align",
});

export default LinearAlignForm;
