import { FunctionComponent, useEffect, useMemo } from "react";
import {
  Alert,
  Button,
  Card,
  Divider,
  Group,
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

const TaskName = "Two-Point Fit";

function convertToAction(
  r: { hour: number; min: number; sec: number; ms: number }, // offset to zero
  o: { hour: number; min: number; sec: number; ms: number }, // offset
  s: { from: number; to: number }, // scale
) {
  return `two_point_fit(rh=${r.hour},rm=${r.min},rs=${r.sec},rms=${r.ms},oh=${o.hour},om=${o.min},os=${o.sec},oms=${o.ms},from=${s.from},to=${s.to})`;
}

const totalMs = (t: { hour: number; min: number; sec: number; ms: number }) =>
  t.hour * 3600000 + t.min * 60000 + t.sec * 1000 + t.ms;

const lineStartMs = (t: SubtitleContents.LineTime) =>
  t.total_seconds * 1000 + Math.round(t.microseconds / 1000);

const lineStartToTime = (t: SubtitleContents.LineTime) => ({
  hour: t.hours,
  min: t.minutes,
  sec: t.seconds,
  ms: Math.round(t.microseconds / 1000),
});

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
    validate: {
      first: {
        line: (v) => (v == null ? "Please select a line" : null),
      },
      last: {
        line: (v, values) => {
          if (v == null) return "Please select a line";
          if (values.first.line != null && v.index === values.first.line.index)
            return "Must be a different line than the first";
          return null;
        },
      },
    },
  });

  // Preselect default lines when data loads
  useEffect(() => {
    if (lines.length === 0) return;

    const firstLine = lines.length < 50 ? lines[0] : lines[9];
    const lastLine =
      lines.length < 50 ? lines[lines.length - 1] : lines[lines.length - 10];

    form.setFieldValue("first.line", firstLine);
    form.setFieldValue("first.to", lineStartToTime(firstLine.start));
    form.setFieldValue("last.line", lastLine);
    form.setFieldValue("last.to", lineStartToTime(lastLine.start));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lines]);

  const wrongOrder = useMemo(() => {
    const { first, last } = form.values;
    if (first.line == null || last.line == null) return false;
    return lineStartMs(first.line.start) >= lineStartMs(last.line.start);
  }, [form.values]);

  const decimals = lines.length.toString().length;
  const options = useSelectorOptions(
    lines,
    (v) =>
      `${String(v.index).padStart(decimals, "0")}: ${String(
        v.content,
      ).replaceAll("\n", " ")}`,
    (v) => String(v.index),
  );

  return (
    <form
      onSubmit={form.onSubmit(({ first, last }) => {
        if (first.line == null || last.line == null) return;

        const r = {
          hour: first.line.start.hours,
          min: first.line.start.minutes,
          sec: first.line.start.seconds,
          ms: Math.round(first.line.start.microseconds / 1000),
        };

        const scale = {
          from: totalMs(last.to) - totalMs(first.to),
          to: lineStartMs(last.line.start) - lineStartMs(first.line.start),
        };

        const action = convertToAction(r, first.to, scale);

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
        {wrongOrder && (
          <Alert color="yellow" variant="filled">
            The first sentence appears after the last sentence in the subtitle
            file. Are the selections correct?
          </Alert>
        )}
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
                onChange={(line: SubtitleContents.Line | null) => {
                  form.setFieldValue("first.line", line);
                  if (line) {
                    form.setFieldValue("first.to", lineStartToTime(line.start));
                  }
                }}
              ></Selector>
            </Stack>

            <Stack gap="0">
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
                onChange={(line: SubtitleContents.Line | null) => {
                  form.setFieldValue("last.line", line);
                  if (line) {
                    form.setFieldValue("last.to", lineStartToTime(line.start));
                  }
                }}
              ></Selector>
            </Stack>

            <Stack gap="0">
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
    title: "Two-Point Fit",
  },
);

export default TwoPointFitForm;
