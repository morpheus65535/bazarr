import { Selector } from "@/components";
import { withModal } from "@/modules/modals";
import { submodProcessColor } from "@/utilities";
import { Button, Divider, Stack } from "@mantine/core";
import { FunctionComponent, useCallback, useState } from "react";
import { useProcess } from ".";
import { colorOptions } from "./tools";

const ColorTool: FunctionComponent = () => {
  const [selection, setSelection] = useState<Nullable<string>>(null);

  const process = useProcess([]);

  const submit = useCallback(() => {
    if (selection) {
      const action = submodProcessColor(selection);
      process(action);
    }
  }, [process, selection]);

  return (
    <Stack>
      <Selector options={colorOptions} onChange={setSelection}></Selector>
      <Divider></Divider>
      <Button disabled={selection === null} onClick={submit}>
        Save
      </Button>
    </Stack>
  );
};

export default withModal(ColorTool, "color-tool");
