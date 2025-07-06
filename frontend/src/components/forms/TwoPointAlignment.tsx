import { FunctionComponent } from "react";
import {
  Button,
  Card,
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
// import FormUtils from "@/utilities/form";

const TaskName = "Linearly Aligning";

function convertToAction(
  r: { hour: number; min: number; sec: number; ms: number }, // offset to zero
  o: { hour: number; min: number; sec: number; ms: number }, // offset
  s: { from: number; to: number }, // scale
) {
  return `two_point_alignment(rh=${r.hour},rm=${r.min},rs=${r.sec},rms=${r.ms},oh=${o.hour},om=${o.min},os=${o.sec},oms=${o.ms},from=${s.from},to=${s.to})`;
}

const totalMs = (t: { hour: number; min: number; sec: number; ms: number }) =>
  t.hour * 3600000 + t.min * 60000 + t.sec * 1000 + t.ms;

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

const TwoPointAlignmentForm: FunctionComponent<Props> = ({
  selections,
  onSubmit,
}) => {
  const { mutateAsync } = useSubtitleAction();
  const modals = useModals();

  const timeInput = {
    hour: 0,
    min: 0,
    sec: 0,
    ms: 0,
    totalMs() {
      return totalMs(this);
    },
  };
  const alignInput = { from: timeInput, to: timeInput };

  const form = useForm({
    initialValues: {
      first: alignInput,
      last: alignInput,
    },
  });

  const enabled =
    (totalMs(form.values.first.from) > 0 ||
      totalMs(form.values.first.to) > 0 ||
      totalMs(form.values.last.from) > 0 ||
      totalMs(form.values.last.to) > 0) &&
    totalMs(form.values.first.to) <= totalMs(form.values.last.to) &&
    totalMs(form.values.first.from) <= totalMs(form.values.last.from);

  return (
    <form
      onSubmit={form.onSubmit(({ first, last }) => {
        const scale = {
          from: last.to.totalMs() - first.to.totalMs(),
          to: last.from.totalMs() - first.from.totalMs(),
        };

        const action: string = convertToAction(first.from, first.to, scale);

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
        <Card>
          <Stack gap="md">
            <header>First sentence</header>
            <Stack gap="0">
              <InputLabel>When it appears</InputLabel>
              <Group align="end" gap="xs" wrap="nowrap">
                <NumberInput
                  label="hour"
                  min={0}
                  {...form.getInputProps("first.from.hour")}
                ></NumberInput>
                <NumberInput
                  label="min"
                  min={0}
                  {...form.getInputProps("first.from.min")}
                ></NumberInput>
                <NumberInput
                  label="sec"
                  min={0}
                  {...form.getInputProps("first.from.sec")}
                ></NumberInput>
                <NumberInput
                  label="ms"
                  min={0}
                  {...form.getInputProps("first.from.ms")}
                ></NumberInput>
              </Group>
            </Stack>

            <Stack gap="0">
              <InputLabel>When it should appear</InputLabel>
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
            </Stack>
          </Stack>
        </Card>

        <Card>
          <Stack gap="md">
            <header>Last sentence</header>
            <Stack gap="0">
              <InputLabel>When it appears</InputLabel>
              <Group align="end" gap="xs" wrap="nowrap">
                <NumberInput
                  min={0}
                  label="hour"
                  {...form.getInputProps("last.from.hour")}
                ></NumberInput>
                <NumberInput
                  min={0}
                  label="min"
                  {...form.getInputProps("last.from.min")}
                ></NumberInput>
                <NumberInput
                  min={0}
                  label="sec"
                  {...form.getInputProps("last.from.sec")}
                ></NumberInput>
                <NumberInput
                  min={0}
                  label="ms"
                  {...form.getInputProps("last.from.ms")}
                ></NumberInput>
              </Group>
            </Stack>

            <Stack gap="0">
              <InputLabel>When it should appear</InputLabel>
              <Group align="end" gap="xs" wrap="nowrap">
                <NumberInput
                  min={0}
                  label="hour"
                  {...form.getInputProps("last.to.hour")}
                ></NumberInput>
                <NumberInput
                  min={0}
                  label="min"
                  {...form.getInputProps("last.to.min")}
                ></NumberInput>
                <NumberInput
                  min={0}
                  label="sec"
                  {...form.getInputProps("last.to.sec")}
                ></NumberInput>
                <NumberInput
                  min={0}
                  label="ms"
                  {...form.getInputProps("last.to.ms")}
                ></NumberInput>
              </Group>
            </Stack>
          </Stack>
        </Card>

        <Divider></Divider>
        <Button disabled={!enabled} type="submit">
          Start
        </Button>
      </Stack>
    </form>
  );
};

export const TwoPointAlignmentModal = withModal(
  TwoPointAlignmentForm,
  "two-point-alignment",
  {
    title: "Linear Align",
  },
);

export default TwoPointAlignmentForm;
