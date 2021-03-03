import {
  faClock,
  faCloudUploadAlt,
  faDownload,
  faRecycle,
  faTrash,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";
import moment from "moment";
import React, {
  ChangeEvent,
  FunctionComponent,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Form,
  OverlayTrigger,
  Popover,
  Spinner,
  SpinnerProps,
} from "react-bootstrap";

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

interface MessageIconProps extends FontAwesomeIconProps {
  messages: string[];
}

export const MessageIcon: FunctionComponent<MessageIconProps> = (props) => {
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

export const LoadingIndicator: FunctionComponent<{
  animation?: SpinnerProps["animation"];
}> = ({ children, animation: style }) => {
  return (
    <div className="d-flex flex-column flex-grow-1 align-items-center py-5">
      <Spinner animation={style ?? "border"} className="mb-2"></Spinner>
      {children}
    </div>
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

interface FormatterProps {
  format?: string;
  children: string;
}

export const DateFormatter: FunctionComponent<FormatterProps> = ({
  children,
  format,
}) => {
  const result = useMemo(
    () => moment(children, format ?? "DD/MM/YYYY h:mm:ss").fromNow(),
    [children, format]
  );
  return <span>{result}</span>;
};

interface SubtitleProps {
  subtitle: Subtitle;
  name?: boolean;
  className?: string;
}

export const SubtitleText: FunctionComponent<SubtitleProps> = ({
  subtitle,
  className,
  name,
}) => {
  const text = useMemo(() => {
    const useName = name ?? false;
    let result = useName ? subtitle.name : subtitle.code2;
    if (subtitle.hi) {
      result += ":HI";
    } else if (subtitle.forced) {
      result += ":Forced";
    }
    return result;
  }, [subtitle, name]);
  return <span className={className}>{text}</span>;
};

export * from "./async";
export * from "./buttons";
export * from "./ContentHeader";
export * from "./inputs";
export { default as ItemOverview } from "./ItemOverview";
export { default as LanguageSelector } from "./LanguageSelector";
export * from "./modals";
export * from "./SearchBar";
export * from "./tables";
