import {
  faBug,
  faCircleNotch,
  faExclamationTriangle,
  faInfoCircle,
  faStream,
  IconDefinition,
} from "@fortawesome/free-solid-svg-icons";
import {
  FontAwesomeIcon,
  FontAwesomeIconProps,
} from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Button,
  Dropdown,
  Overlay,
  ProgressBar,
  Tooltip,
} from "react-bootstrap";
import { useDidUpdate, useTimeoutWhen } from "rooks";
import { useReduxStore } from "../@redux/hooks/base";
import { BuildKey, useIsArrayExtended } from "../utilites";
import "./notification.scss";

enum State {
  Idle,
  Working,
  Failed,
}

function useTotalProgress(progress: Site.Progress[]) {
  return useMemo(() => {
    const { value, count } = progress.reduce(
      (prev, { value, count }) => {
        prev.value += value;
        prev.count += count;
        return prev;
      },
      { value: 0, count: 0 }
    );

    if (count === 0) {
      return 0;
    } else {
      return (value + 0.001) / count;
    }
  }, [progress]);
}

function useHasErrorNotification(notifications: Server.Notification[]) {
  return useMemo(
    () => notifications.find((v) => v.type !== "info") !== undefined,
    [notifications]
  );
}

const NotificationCenter: FunctionComponent = () => {
  const { progress, notifications, notifier } = useReduxStore((s) => s.site);

  const dropdownRef = useRef<HTMLDivElement>(null);
  const [hasNew, setHasNew] = useState(false);

  const hasNewProgress = useIsArrayExtended(progress);
  const hasNewNotifications = useIsArrayExtended(notifications);
  useDidUpdate(() => {
    if (hasNewNotifications || hasNewProgress) {
      setHasNew(true);
    }
  }, [hasNewProgress, hasNewNotifications]);

  const [btnState, setBtnState] = useState(State.Idle);

  const totalProgress = useTotalProgress(progress);
  const hasError = useHasErrorNotification(notifications);

  useEffect(() => {
    if (hasError) {
      setBtnState(State.Failed);
    } else if (totalProgress > 0) {
      setBtnState(State.Working);
    } else if (totalProgress <= 0) {
      setBtnState(State.Idle);
    }
  }, [totalProgress, hasError]);

  const iconProps = useMemo<FontAwesomeIconProps>(() => {
    switch (btnState) {
      case State.Idle:
        return {
          icon: faStream,
        };
      case State.Working:
        return {
          icon: faCircleNotch,
          spin: true,
        };
      default:
        return {
          icon: faExclamationTriangle,
        };
    }
  }, [btnState]);

  const content = useMemo<React.ReactNode>(() => {
    const nodes: JSX.Element[] = [];

    nodes.push(
      <Dropdown.Header key="notifications-header">
        {notifications.length > 0 ? "Notifications" : "No Notifications"}
      </Dropdown.Header>
    );
    nodes.push(
      ...notifications.map((v, idx) => (
        <Dropdown.Item disabled key={BuildKey(idx, v.id, "notification")}>
          <Notification {...v}></Notification>
        </Dropdown.Item>
      ))
    );

    nodes.push(<Dropdown.Divider key="dropdown-divider"></Dropdown.Divider>);

    nodes.push(
      <Dropdown.Header key="background-task-header">
        {progress.length > 0 ? "Background Tasks" : "No Background Tasks"}
      </Dropdown.Header>
    );
    nodes.push(
      ...progress.map((v, idx) => (
        <Dropdown.Item disabled key={BuildKey(idx, v.id, "progress")}>
          <Progress {...v}></Progress>
        </Dropdown.Item>
      ))
    );

    return nodes;
  }, [progress, notifications]);

  const onToggleClick = useCallback(() => {
    setHasNew(false);
  }, []);

  // Tooltip Controller
  const [showTooltip, setTooltip] = useState(false);
  useTimeoutWhen(() => setTooltip(false), 3 * 1000, showTooltip);
  useDidUpdate(() => {
    if (notifier.content) {
      setTooltip(true);
    }
  }, [notifier.update]);

  return (
    <React.Fragment>
      <Dropdown
        onClick={onToggleClick}
        className={`notification-btn ${hasNew ? "new-item" : ""}`}
        ref={dropdownRef}
        alignRight
      >
        <Dropdown.Toggle as={Button} className="dropdown-hidden">
          <FontAwesomeIcon {...iconProps}></FontAwesomeIcon>
        </Dropdown.Toggle>
        <Dropdown.Menu className="pb-3">{content}</Dropdown.Menu>
      </Dropdown>
      <Overlay target={dropdownRef} show={showTooltip} placement="bottom">
        {(props) => {
          return (
            <Tooltip id="new-notification-tip" {...props}>
              {notifier.content}
            </Tooltip>
          );
        }}
      </Overlay>
    </React.Fragment>
  );
};

const Notification: FunctionComponent<Server.Notification> = ({
  type,
  message,
}) => {
  const icon = useMemo<IconDefinition>(() => {
    switch (type) {
      case "info":
        return faInfoCircle;
      case "warning":
        return faExclamationTriangle;
      default:
        return faBug;
    }
  }, [type]);
  return (
    <div className="notification-center-notification d-flex flex-nowrap align-items-center justify-content-start my-1">
      <FontAwesomeIcon className="mr-2 text-dark" icon={icon}></FontAwesomeIcon>
      <span className="text-dark small">{message}</span>
    </div>
  );
};

const Progress: FunctionComponent<Site.Progress> = ({
  name,
  value,
  count,
  header,
}) => {
  const isCompleted = value / count > 1;
  const displayValue = Math.min(count, value + 1);
  return (
    <div className="notification-center-progress d-flex flex-column">
      <p className="progress-header m-0 h-6 text-dark font-weight-bold">
        {header}
      </p>
      <p className="progress-name m-0 small text-secondary">
        {isCompleted ? "Completed successfully" : name}
      </p>
      <ProgressBar
        className="mt-2"
        animated={!isCompleted}
        now={displayValue / count}
        max={1}
        label={`${displayValue}/${count}`}
      ></ProgressBar>
    </div>
  );
};

export default NotificationCenter;
