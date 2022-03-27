import { useModal, withModal } from "@/modules/modals";
import { faMinus, faPlus } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  ChangeEventHandler,
  FunctionComponent,
  useCallback,
  useState,
} from "react";
import { Button, Form, InputGroup } from "react-bootstrap";
import { useProcess } from "./ToolContext";

function submodProcessOffset(h: number, m: number, s: number, ms: number) {
  return `shift_offset(h=${h},m=${m},s=${s},ms=${ms})`;
}

const TimeAdjustmentTool: FunctionComponent = () => {
  const [isPlus, setPlus] = useState(true);
  const [offset, setOffset] = useState<[number, number, number, number]>([
    0, 0, 0, 0,
  ]);

  const Modal = useModal();

  const updateOffset = useCallback(
    (idx: number): ChangeEventHandler<HTMLInputElement> => {
      return (e) => {
        let value = parseFloat(e.currentTarget.value);
        if (isNaN(value)) {
          value = 0;
        }
        const newOffset = [...offset] as [number, number, number, number];
        newOffset[idx] = value;
        setOffset(newOffset);
      };
    },
    [offset]
  );

  const canSave = offset.some((v) => v !== 0);

  const process = useProcess();

  const submit = useCallback(() => {
    if (canSave) {
      const newOffset = offset.map((v) => (isPlus ? v : -v));
      const action = submodProcessOffset(
        newOffset[0],
        newOffset[1],
        newOffset[2],
        newOffset[3]
      );
      process(action);
    }
  }, [canSave, offset, process, isPlus]);

  const footer = (
    <Button disabled={!canSave} onClick={submit}>
      Save
    </Button>
  );

  return (
    <Modal title="Adjust Times" footer={footer}>
      <InputGroup>
        <InputGroup.Prepend>
          <Button
            variant="secondary"
            title={isPlus ? "Later" : "Earlier"}
            onClick={() => setPlus(!isPlus)}
          >
            <FontAwesomeIcon icon={isPlus ? faPlus : faMinus}></FontAwesomeIcon>
          </Button>
        </InputGroup.Prepend>
        <Form.Control
          type="number"
          placeholder="hour"
          onChange={updateOffset(0)}
        ></Form.Control>
        <Form.Control
          type="number"
          placeholder="min"
          onChange={updateOffset(1)}
        ></Form.Control>
        <Form.Control
          type="number"
          placeholder="sec"
          onChange={updateOffset(2)}
        ></Form.Control>
        <Form.Control
          type="number"
          placeholder="ms"
          onChange={updateOffset(3)}
        ></Form.Control>
      </InputGroup>
    </Modal>
  );
};

export default withModal(TimeAdjustmentTool, "time-adjustment");
