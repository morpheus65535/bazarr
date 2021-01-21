import React, { FunctionComponent, useMemo, useState } from "react";
import { Dropdown, Form } from "react-bootstrap";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { faCheck } from "@fortawesome/free-solid-svg-icons";

type SelectorBasic<T extends string | string[]> = {
  className?: string;
  options: LooseObject | Pair[];
  disabled?: boolean;
  nullKey?: string;
  defaultKey?: T;
  onSelect?: (key: string) => void;
  onMultiSelect?: (keys: string[]) => void;
};

export type SingleSelectorProps = {
  multiply?: false;
} & SelectorBasic<string>;

export type MultiSelectorProps = {
  multiply: true;
} & SelectorBasic<string[]>;

export type SelectorProps = SingleSelectorProps | MultiSelectorProps;

export const Selector: FunctionComponent<SelectorProps> = (props) => {
  const { className, disabled, options, nullKey, ...other } = props;
  const [filter, setFilter] = useState("");

  const initializeKey: string[] = useMemo(() => {
    if (other.multiply) {
      if (other.defaultKey) {
        return other.defaultKey;
      } else if (nullKey) {
        return [nullKey];
      } else {
        return [];
      }
    } else {
      if (other.defaultKey) {
        return [other.defaultKey];
      } else if (nullKey) {
        return [nullKey];
      } else {
        return [];
      }
    }
  }, [nullKey, other]);

  const [selectKey, setSelect] = useState(initializeKey);

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
      return pairs.filter((p) =>
        p.value.toLowerCase().includes(filter.toLowerCase())
      );
    }
  }, [pairs, filter]);

  const items = useMemo(() => {
    function updateSelection(key: string) {
      const newSelect = selectKey.slice();
      const oldIndex = newSelect.findIndex((v) => v === key);

      if (oldIndex === -1) {
        if (other.multiply) {
          newSelect.push(key);
        } else {
          newSelect[0] = key;
        }
      } else if (other.multiply) {
        newSelect.splice(oldIndex, 1);
      }

      setSelect(newSelect);
      if (other.multiply) {
        other.onMultiSelect && other.onMultiSelect(newSelect);
      } else {
        other.onSelect && other.onSelect(newSelect[0]);
      }
    }

    return avaliable.map((p) => {
      const hasCheck = other.multiply && selectKey.includes(p.key);
      return (
        <Dropdown.Item
          key={p.key}
          className="d-flex justify-content-between align-items-center"
          onClick={(e) => {
            e.preventDefault();
            updateSelection(p.key);
          }}
        >
          <span>{p.value}</span>
          {hasCheck && <FontAwesomeIcon icon={faCheck}></FontAwesomeIcon>}
        </Dropdown.Item>
      );
    });
  }, [avaliable, selectKey, setSelect, other]);

  const title = useMemo(() => {
    let text: string;

    if (selectKey.length !== 0) {
      if (options instanceof Array) {
        text = selectKey
          .map((s) => options.find((v) => v.key === s)!.value)
          .join(", ");
      } else {
        text = selectKey.map((s) => options[s]).join(", ");
      }
    } else {
      text = "Select...";
    }
    return text;
  }, [selectKey, options]);

  return (
    <Dropdown defaultValue={selectKey} className={className}>
      <Dropdown.Toggle
        disabled={disabled}
        block
        className="text-left"
        variant="outline-secondary"
      >
        {title}
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
