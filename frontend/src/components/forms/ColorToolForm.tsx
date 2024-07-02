import { FunctionComponent } from "react";
import { Button, Divider, Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useSubtitleAction } from "@/apis/hooks";
import { Selector, SelectorOption } from "@/components";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import FormUtils from "@/utilities/form";

const TaskName = "Changing Color";

function convertToAction(color: string) {
  return `color(name=${color})`;
}

export const colorOptions: SelectorOption<string>[] = [
  {
    label: "White",
    value: "white",
  },
  {
    label: "Light Gray",
    value: "light-gray",
  },
  {
    label: "Red",
    value: "red",
  },
  {
    label: "Green",
    value: "green",
  },
  {
    label: "Yellow",
    value: "yellow",
  },
  {
    label: "Blue",
    value: "blue",
  },
  {
    label: "Magenta",
    value: "magenta",
  },
  {
    label: "Cyan",
    value: "cyan",
  },
  {
    label: "Black",
    value: "black",
  },
  {
    label: "Dark Red",
    value: "dark-red",
  },
  {
    label: "Dark Green",
    value: "dark-green",
  },
  {
    label: "Dark Yellow",
    value: "dark-yellow",
  },
  {
    label: "Dark Blue",
    value: "dark-blue",
  },
  {
    label: "Dark Magenta",
    value: "dark-magenta",
  },
  {
    label: "Dark Cyan",
    value: "dark-cyan",
  },
  {
    label: "Dark Grey",
    value: "dark-grey",
  },
];

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

const ColorToolForm: FunctionComponent<Props> = ({ selections, onSubmit }) => {
  const { mutateAsync } = useSubtitleAction();
  const modals = useModals();

  const form = useForm({
    initialValues: {
      color: "",
    },
    validate: {
      color: FormUtils.validation(
        (value) => colorOptions.find((op) => op.value === value) !== undefined,
        "Must select a color",
      ),
    },
  });

  return (
    <form
      onSubmit={form.onSubmit(({ color }) => {
        const action = convertToAction(color);

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
        <Selector
          required
          options={colorOptions}
          {...form.getInputProps("color")}
        ></Selector>
        <Divider></Divider>
        <Button type="submit">Start</Button>
      </Stack>
    </form>
  );
};

export const ColorToolModal = withModal(ColorToolForm, "color-tool", {
  title: "Change Color",
});

export default ColorToolForm;
