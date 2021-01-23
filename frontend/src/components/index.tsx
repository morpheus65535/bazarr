import React, {
  FunctionComponent,
  ChangeEvent,
  useState,
  useMemo,
  useEffect,
  useRef,
} from "react";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";
import { Spinner, Form, OverlayTrigger, Popover } from "react-bootstrap";
import {
  faCheck,
  faTimes,
  faTrash,
  faDownload,
  faUser,
  faRecycle,
  faCloudUploadAlt,
  faClock,
} from "@fortawesome/free-solid-svg-icons";

enum HistoryAction {
  Delete = 0,
  Download,
  Manual,
  Upgrade,
  Upload,
  Sync,
}

export const HistoryIcon: FunctionComponent<{ action: number }> = (props) => {
  const { action } = props;
  let icon = null;
  switch (action) {
    case HistoryAction.Delete:
      icon = faTrash;
      break;
    case HistoryAction.Download:
      icon = faDownload;
      break;
    case HistoryAction.Manual:
      icon = faUser;
      break;
    case HistoryAction.Sync:
      icon = faClock;
      break;
    case HistoryAction.Upgrade:
      icon = faRecycle;
      break;
    case HistoryAction.Upload:
      icon = faCloudUploadAlt;
      break;
  }
  if (icon) {
    return <FontAwesomeIcon icon={icon}></FontAwesomeIcon>;
  } else {
    return null;
  }
};

interface OverlayIconProps extends FontAwesomeIconProps {
  messages: string[];
}

export const OverlayIcon: FunctionComponent<OverlayIconProps> = (props) => {
  const { messages, ...iconProps } = props;

  const popover = (
    <Popover hidden={messages.length === 0} id="overlay-icon">
      <Popover.Content>
        {messages.map((m) => (
          <li key={m}>{m}</li>
        ))}
      </Popover.Content>
    </Popover>
  );

  return (
    <OverlayTrigger overlay={popover}>
      <FontAwesomeIcon {...iconProps}></FontAwesomeIcon>
    </OverlayTrigger>
  );
};

export const LoadingIndicator: FunctionComponent = ({ children }) => {
  return (
    <div className="d-flex flex-column flex-grow-1 align-items-center justify-content-center py-5">
      <Spinner animation="border" className="mb-2"></Spinner>
      {children}
    </div>
  );
};

export const BooleanIndicator: FunctionComponent<{ value: boolean }> = (
  props
) => {
  return (
    <FontAwesomeIcon icon={props.value ? faCheck : faTimes}></FontAwesomeIcon>
  );
};

interface FileFormProps {
  disabled?: boolean;
  multiple?: boolean;
  emptyText: string;
  files?: File[];
  onChange?: (files: File[]) => void;
}

export const FileForm: FunctionComponent<FileFormProps> = ({
  files,
  emptyText,
  multiple,
  disabled,
  onChange,
}) => {
  const [fileList, setFileList] = useState<File[]>([]);

  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (files) {
      setFileList(files);

      if (files.length === 0 && input.current) {
        // Manual reset file input
        input.current.value = "";
      }
    }
  }, [files]);

  const label = useMemo(() => {
    if (fileList.length === 0) {
      return emptyText;
    } else {
      if (multiple) {
        return `${fileList.length} Files`;
      } else {
        return fileList[0].name;
      }
    }
  }, [fileList, emptyText, multiple]);

  return (
    <Form.File
      disabled={disabled}
      custom
      label={label}
      multiple={multiple}
      ref={input}
      onChange={(e: ChangeEvent<HTMLInputElement>) => {
        const { files } = e.target;
        if (files) {
          const list: File[] = [];
          for (const file of files) {
            list.push(file);
          }
          setFileList(list);
          onChange && onChange(list);
        }
      }}
    ></Form.File>
  );
};

export { default as ItemOverview } from "./ItemOverview";
export { default as LanguageSelector } from "./LanguageSelector";
export { default as AsyncStateOverlay } from "./AsyncStateOverlay";
export * from "./Modals";
export * from "./ContentHeader";
export * from "./Tables";
export * from "./Selector";
export * from "./Slider";
export * from "./SearchBar";
export * from "./buttons";
