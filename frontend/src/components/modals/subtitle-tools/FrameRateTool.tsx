import { withModal } from "@/modules/modals";
import { Button, Divider, Group, NumberInput, Stack } from "@mantine/core";
import { FunctionComponent, useCallback, useState } from "react";
import { useProcess } from ".";

function submodProcessFrameRate(from: number, to: number) {
  return `change_FPS(from=${from},to=${to})`;
}

const FrameRateTool: FunctionComponent = () => {
  const [from, setFrom] = useState<Nullable<number>>(null);
  const [to, setTo] = useState<Nullable<number>>(null);

  const canSave = from !== null && to !== null && from !== to;

  const process = useProcess([]);

  const submit = useCallback(() => {
    if (canSave) {
      const action = submodProcessFrameRate(from, to);
      process(action);
    }
  }, [canSave, from, process, to]);

  return (
    <Stack>
      <Group spacing="xs">
        <NumberInput
          placeholder="From"
          onChange={(num) => setFrom(num ?? null)}
        ></NumberInput>
        <NumberInput
          placeholder="To"
          onChange={(num) => setTo(num ?? null)}
        ></NumberInput>
      </Group>
      <Divider></Divider>
      <Button disabled={!canSave} onClick={submit}>
        Save
      </Button>
    </Stack>
  );
};

export default withModal(FrameRateTool, "frame-rate-tool");
