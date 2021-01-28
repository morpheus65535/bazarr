import React, {
  FunctionComponent,
  KeyboardEvent,
  FocusEvent,
  useCallback,
  useMemo,
  useRef,
  useState,
} from "react";
import "./chip.scss";

export interface ChipsProps {
  disabled?: boolean;
  defaultValue?: string[];
  onChange?: (v: string[]) => void;
}

export const Chips: FunctionComponent<ChipsProps> = ({
  defaultValue,
  disabled,
  onChange,
}) => {
  const [chips, setChips] = useState<string[]>(defaultValue ?? []);

  const input = useRef<HTMLInputElement>(null);

  const addChip = useCallback(
    (value: string) => {
      const newChips = [...chips];
      newChips.push(value);
      setChips(newChips);
      onChange && onChange(newChips);
    },
    [chips, onChange]
  );

  const removeChip = useCallback(
    (idx?: number) => {
      idx = idx ?? chips.length - 1;
      if (idx !== -1) {
        const newChips = [...chips];
        newChips.splice(idx, 1);
        setChips(newChips);
        onChange && onChange(newChips);
      }
    },
    [chips, onChange]
  );

  const clearInput = useCallback(() => {
    if (input.current) {
      input.current.value = "";
    }
  }, [input]);

  const onKeyUp = useCallback(
    (event: KeyboardEvent<HTMLInputElement>) => {
      const pressed = event.key;
      const value = event.currentTarget.value;
      if ((pressed === "Tab" || pressed === "Enter") && value.length !== 0) {
        event.preventDefault();
        addChip(value);
        clearInput();
      } else if (pressed === "Backspace" && value.length === 0) {
        event.preventDefault();
        removeChip();
      }
    },
    [addChip, removeChip, clearInput]
  );

  const onKeyDown = useCallback((event: KeyboardEvent<HTMLInputElement>) => {
    const pressed = event.key;
    const value = event.currentTarget.value;
    if ((pressed === "Tab" || pressed === "Enter") && value.length !== 0) {
      event.preventDefault();
    }
  }, []);

  const onBlur = useCallback(
    (event: FocusEvent<HTMLInputElement>) => {
      const value = event.currentTarget.value;
      if (value.length !== 0) {
        event.preventDefault();
        addChip(value);
        clearInput();
      }
    },
    [addChip, clearInput]
  );

  const chipElements = useMemo(
    () =>
      chips.map((v, idx) => (
        <span
          // TODO: Element Disabled
          key={idx}
          title={v}
          className="custom-chip"
          onClick={() => removeChip(idx)}
        >
          {v}
        </span>
      )),
    [chips, removeChip]
  );

  return (
    <div className="form-control custom-chip-input d-flex">
      <div className="chip-container">{chipElements}</div>
      <input
        disabled={disabled}
        className="main-input p-0"
        ref={input}
        onKeyUp={onKeyUp}
        onKeyDown={onKeyDown}
        onBlur={onBlur}
      ></input>
    </div>
  );
};
