import clsx from "clsx";
import React, {
  FocusEvent,
  FunctionComponent,
  KeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

const SplitKeys = ["Tab", "Enter", " ", ",", ";"];

export interface ChipsProps {
  disabled?: boolean;
  defaultValue?: readonly string[];
  value?: readonly string[];
  onChange?: (v: string[]) => void;
}

export const Chips: FunctionComponent<ChipsProps> = ({
  defaultValue,
  value,
  disabled,
  onChange,
}) => {
  const [chips, setChips] = useState<Readonly<string[]>>(() => {
    if (value) {
      return value;
    }
    if (defaultValue) {
      return defaultValue;
    }
    return [];
  });

  useEffect(() => {
    if (value) {
      setChips(value);
    }
  }, [value]);

  const input = useRef<HTMLInputElement>(null);

  const addChip = useCallback(
    (value: string) => {
      setChips((cp) => {
        const newChips = [...cp, value];
        onChange && onChange(newChips);
        return newChips;
      });
    },
    [onChange]
  );

  const removeChip = useCallback(
    (idx?: number) => {
      setChips((cp) => {
        const index = idx ?? cp.length - 1;
        if (index !== -1) {
          const newChips = [...cp];
          newChips.splice(index, 1);
          onChange && onChange(newChips);
          return newChips;
        } else {
          return cp;
        }
      });
    },
    [onChange]
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
      if (SplitKeys.includes(pressed) && value.length !== 0) {
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
    if (SplitKeys.includes(pressed) && value.length !== 0) {
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
          key={idx}
          title={v}
          className={clsx("element", { active: disabled !== true })}
          onClick={() => {
            if (!disabled) {
              removeChip(idx);
            }
          }}
        >
          {v}
        </span>
      )),
    [chips, removeChip, disabled]
  );

  return (
    <div className={clsx("chip-container", "form-control d-flex")}>
      <div className="chips">{chipElements}</div>
      <input
        disabled={disabled}
        className={clsx("p-0", "input")}
        ref={input}
        onKeyUp={onKeyUp}
        onKeyDown={onKeyDown}
        onBlur={onBlur}
      ></input>
    </div>
  );
};
