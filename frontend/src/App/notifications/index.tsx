import {
  faExclamationTriangle,
  faPaperPlane,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { capitalize } from "lodash";
import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
} from "react";
import { ProgressBar, Toast } from "react-bootstrap";
import {
  siteRemoveNotifications,
  siteRemoveProgress,
} from "../../@redux/actions";
import { useReduxAction, useReduxStore } from "../../@redux/hooks/base";
import "./style.scss";

export interface NotificationContainerProps {}

const NotificationContainer: FunctionComponent<NotificationContainerProps> = () => {
  const { progress, notifications } = useReduxStore((s) => s.site);

  const items = useMemo(() => {
    const progressItems = progress.map((v) => (
      <ProgressToast key={v.id} {...v}></ProgressToast>
    ));

    const notificationItems = notifications.map((v) => (
      <NotificationToast key={v.id} {...v}></NotificationToast>
    ));

    return [...progressItems, ...notificationItems];
  }, [notifications, progress]);
  return (
    <div className="alert-container">
      <div className="toast-container">{items}</div>
    </div>
  );
};

type MessageHolderProps = Server.Notification & {};

const NotificationToast: FunctionComponent<MessageHolderProps> = (props) => {
  const { message, type, id, timeout } = props;
  const removeNotification = useReduxAction(siteRemoveNotifications);

  const remove = useCallback(() => removeNotification(id), [
    removeNotification,
    id,
  ]);

  useEffect(() => {
    const handle = setTimeout(remove, timeout);
    return () => {
      clearTimeout(handle);
    };
  }, [props, remove, timeout]);

  return (
    <Toast onClose={remove} animation={false}>
      <Toast.Header>
        <FontAwesomeIcon
          className="mr-1"
          icon={faExclamationTriangle}
        ></FontAwesomeIcon>
        <strong className="mr-auto">{capitalize(type)}</strong>
      </Toast.Header>
      <Toast.Body>{message}</Toast.Body>
    </Toast>
  );
};

type ProgressHolderProps = Server.Progress & {};

const ProgressToast: FunctionComponent<ProgressHolderProps> = ({
  id,
  header,
  name,
  value,
  count,
}) => {
  const removeProgress = useReduxAction(siteRemoveProgress);
  const remove = useCallback(() => removeProgress(id), [removeProgress, id]);

  useEffect(() => {
    const handle = setTimeout(remove, 10 * 1000);
    return () => {
      clearTimeout(handle);
    };
  }, [value, remove]);

  const incomplete = value / count < 1;

  return (
    <Toast onClose={remove}>
      <Toast.Header closeButton={false}>
        <FontAwesomeIcon className="mr-2" icon={faPaperPlane}></FontAwesomeIcon>
        <span className="mr-auto">{header}</span>
      </Toast.Header>
      <Toast.Body>
        <span>{name}</span>
        <ProgressBar
          className="my-1"
          animated={incomplete}
          now={value / count}
          max={1}
          label={`${value}/${count}`}
        ></ProgressBar>
      </Toast.Body>
    </Toast>
  );
};

export default NotificationContainer;
