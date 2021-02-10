import { faFile, faFolder } from "@fortawesome/free-regular-svg-icons";
import { faReply } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Dropdown, Form } from "react-bootstrap";
import { LoadingIndicator } from "..";

const backKey = "--back--";

function getLastSeparator(path: string): number {
  let idx = path.lastIndexOf("/");
  if (idx === -1) {
    idx = path.lastIndexOf("\\");
  }
  return idx;
}

interface Props {
  defaultValue?: string;
  load: (path: string) => Promise<FileTree[]>;
}

export const FileBrowser: FunctionComponent<Props> = ({
  defaultValue,
  load,
}) => {
  const [show, canShow] = useState(false);
  const [text, setText] = useState(defaultValue ?? "");
  const [path, setPath] = useState("");

  const filter = useMemo(() => {
    const idx = getLastSeparator(text);
    return text.slice(idx + 1);
  }, [text]);

  const previous = useMemo(() => {
    const idx = getLastSeparator(path.slice(0, -1));
    return path.slice(0, idx + 1);
  }, [path]);

  const [tree, setTree] = useState<FileTree[]>([]);

  const items = useMemo(() => {
    const elements = [];

    if (previous.length !== 0) {
      elements.push(
        <Dropdown.Item eventKey={backKey} key="back">
          <FontAwesomeIcon icon={faReply} className="mr-2"></FontAwesomeIcon>
          <span>Go Back</span>
        </Dropdown.Item>
      );
    }

    elements.push(
      ...tree
        .filter((v) => v.name.startsWith(filter))
        .map((v) => (
          <Dropdown.Item eventKey={v.path} key={v.name}>
            <FontAwesomeIcon
              icon={v.children ? faFolder : faFile}
              className="mr-2"
            ></FontAwesomeIcon>
            <span>{v.name}</span>
          </Dropdown.Item>
        ))
    );

    return elements;
  }, [tree, filter, previous]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (text === path) {
      return;
    }

    if (text.endsWith("/") || text.endsWith("\\")) {
      setPath(text);
    } else {
      const idx = getLastSeparator(text);
      const value = text.slice(0, idx + 1);
      if (value !== path) {
        setPath(value);
      }
    }
  }, [path, text]);

  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setLoading(true);
    load(path)
      .then((res) => {
        setTree(res);
        setError(false);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [path, load]);

  return (
    <Dropdown
      show={show}
      onSelect={(key) => {
        if (!key) {
          return;
        }

        if (key !== backKey) {
          setText(key);
        } else {
          setText(previous);
        }
        input.current?.focus();
      }}
      onToggle={(open, _, meta) => {
        if (!open && meta.source !== "select") {
          canShow(false);
        } else if (open) {
          canShow(true);
        }
      }}
    >
      <Dropdown.Toggle
        as={Form.Control}
        placeholder="Start typing or select a path below"
        type="text"
        value={text}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
          setText(e.currentTarget.value);
        }}
        ref={input}
        isInvalid={error}
      ></Dropdown.Toggle>
      <Dropdown.Menu
        className="w-100"
        style={{ maxHeight: 256, overflowY: "auto" }}
      >
        {loading ? <LoadingIndicator></LoadingIndicator> : items}
      </Dropdown.Menu>
    </Dropdown>
  );
};
