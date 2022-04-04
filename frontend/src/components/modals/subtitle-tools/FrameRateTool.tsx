import { useModal, withModal } from "@/modules/modals";
import { Button } from "@mantine/core";
import { FunctionComponent, useCallback, useState } from "react";
import { useProcess } from "./ToolContext";

function submodProcessFrameRate(from: number, to: number) {
  return `change_FPS(from=${from},to=${to})`;
}

const FrameRateTool: FunctionComponent = () => {
  const [from, setFrom] = useState<Nullable<number>>(null);
  const [to, setTo] = useState<Nullable<number>>(null);

  const canSave = from !== null && to !== null && from !== to;

  const Modal = useModal();

  const process = useProcess();

  const submit = useCallback(() => {
    if (canSave) {
      const action = submodProcessFrameRate(from, to);
      process(action);
    }
  }, [canSave, from, process, to]);

  const footer = (
    <Button disabled={!canSave} onClick={submit}>
      Save
    </Button>
  );

  return (
    <Modal title="Change Frame Rate" footer={footer}>
      {/* <InputGroup className="px-2">
        <Form.Control
          placeholder="From"
          type="number"
          onChange={(e) => {
            const value = parseFloat(e.currentTarget.value);
            if (isNaN(value)) {
              setFrom(null);
            } else {
              setFrom(value);
            }
          }}
        ></Form.Control>
        <Form.Control
          placeholder="To"
          type="number"
          onChange={(e) => {
            const value = parseFloat(e.currentTarget.value);
            if (isNaN(value)) {
              setTo(null);
            } else {
              setTo(value);
            }
          }}
        ></Form.Control>
      </InputGroup> */}
    </Modal>
  );
};

export default withModal(FrameRateTool, "frame-rate-tool");
