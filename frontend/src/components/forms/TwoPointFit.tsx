import { FunctionComponent, useMemo } from "react";
import {
  Alert,
  Button,
  Card,
  Divider,
  Group,
  // InputLabel,
  LoadingOverlay,
  NumberInput,
  Stack,
} from "@mantine/core";
import { useForm } from "@mantine/form";
import { useSubtitleAction, useSubtitleContents } from "@/apis/hooks";
import { Selector } from "@/components/inputs";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import { useSelectorOptions } from "@/utilities";

const TaskName = "Two Point Fit";

function convertToAction(
  r: { hour: number; min: number; sec: number; ms: number }, // offset to zero
  o: { hour: number; min: number; sec: number; ms: number }, // offset
  s: { from: number; to: number }, // scale
) {
  return `two_point_fit(rh=${r.hour},rm=${r.min},rs=${r.sec},rms=${r.ms},oh=${o.hour},om=${o.min},os=${o.sec},oms=${o.ms},from=${s.from},to=${s.to})`;
}

const totalMs = (t: { hour: number; min: number; sec: number; ms: number }) =>
  t.hour * 3600000 + t.min * 60000 + t.sec * 1000 + t.ms;

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

const TwoPointFitForm: FunctionComponent<Props> = ({
  selections,
  onSubmit,
}) => {
  const { mutateAsync } = useSubtitleAction();
  const modals = useModals();

  const query = useSubtitleContents(selections[0].path);
  const lines = useMemo(() => query.data ?? [], [query]);

  const form = useForm({
    initialValues: {
      first: {
        line: null as SubtitleContents.Line | null,
        to: { hour: 0, min: 0, sec: 0, ms: 0 },
      },
      last: {
        line: null as SubtitleContents.Line | null,
        to: { hour: 0, min: 0, sec: 0, ms: 0 },
      },
    },
    // validate: {
    //   first: { line: FormUtils.validation(isObject, "Please select a line") },
    //   last: { line: FormUtils.validation(isObject, "Please select a line") },
    // },
  });

  const decimals = lines.length.toString().length;
  const options = useSelectorOptions(
    lines,
    (v) =>
      `${String(v.index).padStart(decimals, "0")}: ${String(v.content).replaceAll("\n", " ")}`,
    (v) => String(v.index),
  );

  return (
    <form
      onSubmit={form.onSubmit(({ first, last }) => {
        const scale = {
          from: totalMs(last.to) - totalMs(first.to),
          to: totalMs(first.to) - totalMs(last.to),
        };

        const action: string = convertToAction(first.to, first.to, scale);

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
      <LoadingOverlay
        visible={query.isLoading}
        zIndex={1000}
        overlayProps={{ radius: "sm", blur: 2 }}
      />
      <Stack>
        <Alert>
          Select two sentences and the time for when they should appear. This
          will fit (offset and scale) every sentence.
        </Alert>
        <Card>
          <Stack gap="md">
            <header>First sentence</header>
            <Alert variant="outline">
              The closer to the beginning, the better.
            </Alert>
            <Stack gap="0">
              <Selector
                {...options}
                disabled={query.isLoading}
                {...form.getInputProps("first.line")}
              ></Selector>
            </Stack>

            <Stack gap="0">
              {/* <InputLabel>When it should appear</InputLabel> */}
              <Group align="end" gap="xs" wrap="nowrap">
                <NumberInput
                  label="hour"
                  min={0}
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
            <Alert variant="outline">The closer to the end, the better.</Alert>
            <Stack gap="0">
              <Selector
                {...options}
                disabled={query.isLoading}
                {...form.getInputProps("last.line")}
              ></Selector>
            </Stack>

            <Stack gap="0">
              {/* <InputLabel>When it should appear</InputLabel> */}
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
        <Button disabled={query.isLoading} type="submit">
          Align
        </Button>
      </Stack>
    </form>
  );
};

export const TwoPointFitModal = withModal(
  TwoPointFitForm,
  "two-point-alignment",
  {
    title: "Two Point Fit",
  },
);

export default TwoPointFitForm;
