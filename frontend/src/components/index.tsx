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
import { isNull, isUndefined } from "lodash";
import React, { FunctionComponent, useMemo } from "react";
import {
  OverlayTrigger,
  OverlayTriggerProps,
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

export const HistoryIcon: FunctionComponent<{
  action: number;
  title?: string;
}> = (props) => {
  const { action, title } = props;
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
    return <FontAwesomeIcon title={title} icon={icon}></FontAwesomeIcon>;
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

interface LanguageTextProps {
  text: Language.Info;
  className?: string;
  long?: boolean;
}

export const LanguageText: FunctionComponent<LanguageTextProps> = ({
  text,
  className,
  long,
}) => {
  const result = useMemo(() => {
    let lang = text.code2;
    let hi = ":HI";
    let forced = ":Forced";
    if (long) {
      lang = text.name;
      hi = " HI";
      forced = " Forced";
    }

    let res = lang;
    if (text.hi) {
      res += hi;
    } else if (text.forced) {
      res += forced;
    }
    return res;
  }, [text, long]);
  return (
    <span title={text.name} className={className}>
      {result}
    </span>
  );
};

interface TextPopoverProps {
  children: React.ReactElement<any, any>;
  text: string | undefined | null;
  placement?: OverlayTriggerProps["placement"];
  delay?: number;
}

export const TextPopover: FunctionComponent<TextPopoverProps> = ({
  children,
  text,
  placement,
  delay,
}) => {
  if (isNull(text) || isUndefined(text)) {
    return children;
  }

  const popover = (
    <Popover className="mw-100 py-1" id={text}>
      <span className="mx-2">{text}</span>
    </Popover>
  );
  return (
    <OverlayTrigger delay={delay} overlay={popover} placement={placement}>
      {children}
    </OverlayTrigger>
  );
};

export * from "./async";
export * from "./buttons";
export * from "./ContentHeader";
export * from "./inputs";
export * from "./LanguageSelector";
export * from "./modals";
export * from "./SearchBar";
export * from "./tables";
