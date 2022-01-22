import { faFile, faFolder } from "@fortawesome/free-regular-svg-icons";
import { faReply } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { useFileSystem } from "apis/hooks";
import React, {
  FunctionComponent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Dropdown, DropdownProps, Form, Spinner } from "react-bootstrap";

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
  type: "sonarr" | "radarr" | "bazarr";
  onChange?: (path: string) => void;
  drop?: DropdownProps["drop"];
}

export const FileBrowser: FunctionComponent<Props> = ({
  defaultValue,
  type,
  onChange,
  drop,
}) => {
  const [show, canShow] = useState(false);
  const [text, setText] = useState(defaultValue ?? "");
  const [path, setPath] = useState(() => extractPath(text));

  const { data: tree, isFetching } = useFileSystem(type, path, show);

  const filter = useMemo(() => {
    const idx = getLastSeparator(text);
    return text.slice(idx + 1);
  }, [text]);

  const previous = useMemo(() => {
    const idx = getLastSeparator(path.slice(0, -1));
    return path.slice(0, idx + 1);
  }, [path]);

  const requestItems = () => {
    if (isFetching) {
      return (
        <Dropdown.Item>
          <Spinner size="sm" animation="border"></Spinner>
        </Dropdown.Item>
      );
    }

    const elements = [];

    if (tree) {
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
    }

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
  };

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

  return (
    <Dropdown
      show={show}
      drop={drop}
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
        placeholder="Click to start"
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
        {requestItems()}
      </Dropdown.Menu>
    </Dropdown>
  );
};
