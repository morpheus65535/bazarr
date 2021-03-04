import { throttle } from "lodash";
import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Dropdown, Form } from "react-bootstrap";
import { useHistory } from "react-router";

export interface SearchResult {
  name: string;
  link?: string;
}

interface Props {
  className?: string;
  onSearch: (text: string) => SearchResult[];
  onFocus?: () => void;
  onBlur?: () => void;
}

export const SearchBar: FunctionComponent<Props> = ({
  onSearch,
  onFocus,
  onBlur,
  className,
}) => {
  const [text, setText] = useState("");

  const [results, setResults] = useState<SearchResult[]>([]);

  const history = useHistory();

  const updateResult = useMemo(
    () =>
      throttle((text: string) => {
        setResults(onSearch(text));
      }, 500),
    [onSearch]
  );

  const search = useCallback(
    (text: string) => {
      setText(text);
      updateResult(text);
    },
    [updateResult]
  );

  const clear = useCallback(() => {
    setText("");
    setResults([]);
  }, []);

  const items = useMemo(() => {
    const its = results.map((v) => (
      <Dropdown.Item
        key={v.name}
        eventKey={v.link}
        disabled={v.link === undefined}
      >
        <span>{v.name}</span>
      </Dropdown.Item>
    ));

    if (its.length === 0) {
      its.push(<Dropdown.Header key="notify">No Found</Dropdown.Header>);
    }

    return its;
  }, [results]);

  return (
    <Dropdown
      show={text.length !== 0}
      className={className}
      onFocus={onFocus}
      onBlur={onBlur}
      onSelect={(link) => {
        if (link) {
          clear();
          history.push(link);
        }
      }}
    >
      <Form.Control
        type="text"
        size="sm"
        placeholder="Search..."
        value={text}
        onChange={(e) => search(e.currentTarget.value)}
      ></Form.Control>
      <Dropdown.Menu style={{ maxHeight: 256, overflowY: "auto" }}>
        {items}
      </Dropdown.Menu>
    </Dropdown>
  );
};
