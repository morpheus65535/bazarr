import React, { FunctionComponent, useState, useMemo } from "react";
import { useHistory } from "react-router";

import { Dropdown, Form, FormControlProps } from "react-bootstrap";

import { throttle } from "lodash";

export interface SearchResult {
  name: string;
  link?: string;
}

interface ResultItemProps extends SearchResult {
  clear?: () => void;
}

const ResultItem: FunctionComponent<ResultItemProps> = ({
  name,
  link,
  clear,
}) => {
  const history = useHistory();

  return (
    <Dropdown.Item
      disabled={link === undefined}
      onClick={(e) => {
        e.preventDefault();
        clear && clear();
        link && history.push(link);
      }}
    >
      <span>{name}</span>
    </Dropdown.Item>
  );
};

interface Props {
  className?: string;
  onSearch: (text: string) => SearchResult[];
  size?: FormControlProps["size"];
}

export const SearchBar: FunctionComponent<Props> = ({
  onSearch,
  size,
  className,
}) => {
  const [text, setText] = useState("");

  const [results, setResults] = useState<SearchResult[]>([]);

  const search = throttle((text: string) => {
    setText(text);
    setResults(onSearch(text));
  }, 500);

  const clear = () => {
    setText("");
    setResults([]);
  };

  const items = useMemo(() => {
    const its = results.map((val) => (
      <ResultItem {...val} key={val.name} clear={clear}></ResultItem>
    ));

    if (its.length === 0) {
      its.push(<Dropdown.Header key="notify">No Found</Dropdown.Header>);
    }

    return its;
  }, [results]);

  return (
    <Dropdown show={text.length !== 0} className={className}>
      <Form.Control
        type="text"
        size={size}
        placeholder="Search..."
        onChange={(e) => search(e.target.value)}
      ></Form.Control>
      <Dropdown.Menu style={{ maxHeight: 256, overflowY: "auto" }}>
        {items}
      </Dropdown.Menu>
    </Dropdown>
  );
};
