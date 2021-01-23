import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Dropdown, Form } from "react-bootstrap";
import { capitalize } from "lodash";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { faCheck } from "@fortawesome/free-solid-svg-icons";

type SelectorBasic<T extends string | string[]> = {
  className?: string;
  variant?: string;
  options: LooseObject | Pair[];
  disabled?: boolean;
  defaultKey?: T;
  onSelect?: (key: string) => void;
  onMultiSelect?: (keys: string[]) => void;
};

export type SingleSelectorProps = {
  nullKey?: string;
  multiple?: false;
} & SelectorBasic<string>;

export type MultiSelectorProps = {
  multiple: true;
} & SelectorBasic<string[]>;

export type SelectorProps = SingleSelectorProps | MultiSelectorProps;

export const Selector: FunctionComponent<SelectorProps> = (props) => {
  const { className, variant, disabled, options, ...other } = props;
  const [filter, setFilter] = useState("");

  const defaultKey: string[] = useMemo(() => {
    if (other.multiple) {
      if (other.defaultKey) {
        return other.defaultKey;
      } else {
        return [];
      }
    } else {
      if (other.defaultKey) {
        return [other.defaultKey];
      } else if (other.nullKey) {
        return [other.nullKey];
      } else {
        return [];
      }
    }
  }, [other]);

  const [selectKey, setSelect] = useState(defaultKey);

  const pairs = useMemo(() => {
    if (options instanceof Array) {
      return options;
    } else {
      const pairs: Pair[] = [];
      for (const key in options) {
        const value = options[key];
        pairs.push({ key, value });
      }
      return pairs;
    }
  }, [options]);

  const avaliable = useMemo(() => {
    if (filter === "") {
      return pairs;
    } else {
      const text = filter.toLowerCase();
      return pairs.filter((p) => p.value.toLowerCase().includes(text));
    }
  }, [pairs, filter]);

  const updateSelection = useCallback(
    (key: string) => {
      const newSelect = [...selectKey];
      const oldIndex = newSelect.findIndex((v) => v === key);

      if (oldIndex === -1) {
        if (other.multiple) {
          newSelect.push(key);
        } else {
          newSelect[0] = key;
        }
      } else if (other.multiple) {
        newSelect.splice(oldIndex, 1);
      }

      setSelect(newSelect);
      if (other.multiple) {
        other.onMultiSelect && other.onMultiSelect(newSelect);
      } else {
        other.onSelect && other.onSelect(newSelect[0]);
      }
    },
    [other, selectKey]
  );

  const createItem = useCallback(
    (p: Pair, checked?: boolean) => (
      <Dropdown.Item
        key={p.key}
        eventKey={p.key}
        className="d-flex justify-content-between align-items-center"
      >
        <span>{p.value}</span>
        {checked && <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>}
      </Dropdown.Item>
    ),
    []
  );

  const items = useMemo(() => {
    const optionItems = [];

    if (
      !other.multiple &&
      other.nullKey &&
      !avaliable.find((v) => v.key === other.nullKey)
    ) {
      optionItems.push(
        <React.Fragment key="null-holder">
          {createItem({ key: other.nullKey, value: capitalize(other.nullKey) })}
          <Dropdown.Divider key="null-divider"></Dropdown.Divider>
        </React.Fragment>
      );
    }

    optionItems.push(
      ...avaliable.map((p) => {
        const hasCheck = other.multiple && selectKey.includes(p.key);
        return createItem(p, hasCheck);
      })
    );

    return optionItems;
  }, [avaliable, selectKey, other, createItem]);

  const findValue = useCallback(
    (key: string): string => {
      if (options instanceof Array) {
        const text = options.find((v) => v.key === key);
        if (text) {
          return text.value;
        }
      } else {
        if (key in options) {
          return options[key];
        }
      }

      if (!other.multiple && other.nullKey === key) {
        return capitalize(other.nullKey);
      } else {
        return "Unknown";
      }
    },
    [options, other]
  );

  const displayText = useMemo(() => {
    let text: string;

    if (selectKey.length !== 0) {
      text = selectKey.map((s) => findValue(s)).join(", ");
    } else {
      if (!other.multiple && other.nullKey) {
        text = capitalize(other.nullKey);
      } else {
        text = "Select...";
      }
    }
    return text;
  }, [selectKey, other, findValue]);

  return (
    <Dropdown
      defaultValue={selectKey}
      className={className}
      onSelect={(key) => {
        if (key) {
          updateSelection(key);
        }
      }}
    >
      <Dropdown.Toggle
        disabled={disabled}
        block
        className="text-left"
        variant={variant ?? "outline-secondary"}
      >
        {displayText}
      </Dropdown.Toggle>
      <Dropdown.Menu>
        <Dropdown.Header hidden={pairs.length <= 10}>
          <Form.Control
            type="text"
            placeholder="Filter"
            onChange={(e) => {
              setFilter(e.target.value);
            }}
          ></Form.Control>
        </Dropdown.Header>
        <Dropdown.Header hidden={items.length !== 0}>
          No Selection
        </Dropdown.Header>
        <div
          style={{
            maxHeight: 256,
            maxWidth: 320,
            overflowY: "auto",
          }}
        >
          {items}
        </div>
      </Dropdown.Menu>
    </Dropdown>
  );
};
