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
import { Dropdown, Form, Spinner } from "react-bootstrap";

const backKey = "--back--";

function getLastSeparator(path: string): number {
  let idx = path.lastIndexOf("/");
  if (idx === -1) {
    idx = path.lastIndexOf("\\");
  }
  return idx;
}

function extractPath(raw: string) {
  if (raw.endsWith("/") || raw.endsWith("\\")) {
    return raw;
  } else {
    const idx = getLastSeparator(raw);
    return raw.slice(0, idx + 1);
  }
}

interface Props {
  defaultValue?: string;
  load: (path: string) => Promise<FileTree[]>;
  onChange?: (path: string) => void;
}

export const FileBrowser: FunctionComponent<Props> = ({
  defaultValue,
  onChange,
  load,
}) => {
  const [show, canShow] = useState(false);
  const [text, setText] = useState(defaultValue ?? "");
  const [path, setPath] = useState(() => extractPath(text));
  const [loading, setLoading] = useState(true);

  const filter = useMemo(() => {
    const idx = getLastSeparator(text);
    return text.slice(idx + 1);
  }, [text]);

  const previous = useMemo(() => {
    const idx = getLastSeparator(path.slice(0, -1));
    return path.slice(0, idx + 1);
  }, [path]);

  const [tree, setTree] = useState<FileTree[]>([]);

  const requestItems = useMemo(() => {
    if (loading) {
      return (
        <Dropdown.Item>
          <Spinner size="sm" animation="border"></Spinner>
        </Dropdown.Item>
      );
    }

    const elements = [];

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

    if (elements.length === 0) {
      elements.push(<Dropdown.Header key="no-files">No Files</Dropdown.Header>);
    }

    if (previous.length !== 0) {
      return [
        <Dropdown.Item eventKey={backKey} key="back">
          <FontAwesomeIcon icon={faReply} className="mr-2"></FontAwesomeIcon>
          <span>Back</span>
        </Dropdown.Item>,
        <Dropdown.Divider key="back-divider"></Dropdown.Divider>,
        ...elements,
      ];
    } else {
      return elements;
    }
  }, [tree, filter, previous, loading]);

  useEffect(() => {
    if (text === path) {
      return;
    }

    const newPath = extractPath(text);
    if (newPath !== path) {
      setPath(newPath);
      onChange && onChange(newPath);
    }
  }, [path, text, onChange]);

  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (show) {
      setLoading(true);
      load(path)
        .then((res) => {
          setTree(res);
        })
        .finally(() => setLoading(false));
    }
  }, [path, load, show]);

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
      ></Dropdown.Toggle>
      <Dropdown.Menu
        className="w-100"
        style={{ maxHeight: 256, overflowY: "auto" }}
      >
        {requestItems}
      </Dropdown.Menu>
    </Dropdown>
  );
};
