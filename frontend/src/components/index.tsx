import React, {
  FunctionComponent,
  MouseEvent,
  ChangeEvent,
  useState,
  useMemo,
  PropsWithChildren,
} from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { IconDefinition } from "@fortawesome/fontawesome-common-types";
import { Badge, Spinner, Button, ButtonProps, Form } from "react-bootstrap";
import {
  faCheck,
  faTimes,
  faTrash,
  faDownload,
  faUser,
  faRecycle,
  faCloudUploadAlt,
  faClock,
  faCircleNotch,
} from "@fortawesome/free-solid-svg-icons";

export const ActionBadge: FunctionComponent<{
  onClick?: (e: MouseEvent) => void;
}> = (props) => {
  const { children, onClick } = props;
  return (
    <Button
      as={Badge}
      className="mx-1 p-1"
      variant="secondary"
      onClick={onClick}
    >
      {children}
    </Button>
  );
};

export const ActionIcon: FunctionComponent<{
  icon: IconDefinition;
  onClick?: (e: MouseEvent) => void;
}> = (props) => {
  const { icon, onClick } = props;
  return (
    <ActionBadge onClick={onClick}>
      <FontAwesomeIcon icon={icon}></FontAwesomeIcon>
    </ActionBadge>
  );
};

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

export const LoadingOverlay: FunctionComponent = () => {
  return (
    <div className="d-flex flex-grow-1 justify-content-center my-5">
      <Spinner animation="border"></Spinner>
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

interface AsyncButtonProps<T> {
  variant?: ButtonProps["variant"];
  size?: ButtonProps["size"];
  disabled?: boolean;
  onChange?: (v: boolean) => void;

  promise: () => Promise<T>;
  success?: (result: T) => void;
  error?: () => void;
}

export function AsyncButton<T>(
  props: PropsWithChildren<AsyncButtonProps<T>>
): JSX.Element {
  const {
    children,
    promise,
    success,
    error,
    onChange,
    disabled,
    ...button
  } = props;

  const [loading, setLoading] = useState(false);

  return (
    <Button
      disabled={loading || disabled}
      {...button}
      onClick={() => {
        setLoading(true);
        onChange && onChange(true);
        promise()
          .then(success)
          .catch(error)
          .finally(() => {
            setLoading(false);
            onChange && onChange(false);
          });
      }}
    >
      {loading ? (
        <FontAwesomeIcon icon={faCircleNotch} spin></FontAwesomeIcon>
      ) : (
        children
      )}
    </Button>
  );
}

interface FileFormProps {
  multiple?: boolean;
  emptyText: string;
  onChange?: (files: File[]) => void;
}

export const FileForm: FunctionComponent<FileFormProps> = ({
  emptyText,
  multiple,
  onChange,
}) => {
  const [fileList, setFileList] = useState<File[]>([]);

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
      custom
      label={label}
      multiple={multiple}
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
