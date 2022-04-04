import { Selector } from "@/components";
import { useModal, withModal } from "@/modules/modals";
import { submodProcessColor } from "@/utilities";
import { Button } from "@mantine/core";
import { FunctionComponent, useCallback, useState } from "react";
import { useProcess } from "./ToolContext";
import { colorOptions } from "./tools";

const ColorTool: FunctionComponent = () => {
  const [selection, setSelection] = useState<Nullable<string>>(null);

  const Modal = useModal();

  const process = useProcess();

  const submit = useCallback(() => {
    if (selection) {
      const action = submodProcessColor(selection);
      process(action);
    }
  }, [process, selection]);

  const footer = (
    <Button disabled={selection === null} onClick={submit}>
      Save
    </Button>
  );

  return (
    <Modal title="Choose Color" footer={footer}>
      <Selector options={colorOptions} onChange={setSelection}></Selector>
    </Modal>
  );
};

export default withModal(ColorTool, "color-tool");
