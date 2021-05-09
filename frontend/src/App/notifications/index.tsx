import {
  faExclamationTriangle,
  faPaperPlane,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { capitalize } from "lodash";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { ProgressBar, Toast } from "react-bootstrap";
import { useTimeoutWhen } from "rooks";
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

type MessageHolderProps = ReduxStore.Notification & {};

const NotificationToast: FunctionComponent<MessageHolderProps> = (props) => {
  const { message, type, id, timeout } = props;
  const removeNotification = useReduxAction(siteRemoveNotifications);

  const remove = useCallback(() => removeNotification(id), [
    removeNotification,
    id,
  ]);

  useTimeoutWhen(remove, timeout);

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

type ProgressHolderProps = ReduxStore.Progress & {};

const ProgressToast: FunctionComponent<ProgressHolderProps> = ({
  id,
  name,
  value,
  count,
}) => {
  const removeProgress = useReduxAction(siteRemoveProgress);
  const remove = useCallback(() => removeProgress(id), [removeProgress, id]);

  // TODO: Auto remove

  return (
    <Toast onClose={remove}>
      <Toast.Body>
        <div className="mb-2 mt-1">
          <FontAwesomeIcon
            className="mr-2"
            icon={faPaperPlane}
          ></FontAwesomeIcon>
          <span>{name}</span>
        </div>
        <ProgressBar
          className="my-1"
          animated
          now={value / count}
          max={1}
          label={`${value}/${count}`}
        ></ProgressBar>
      </Toast.Body>
    </Toast>
  );
};

export default NotificationContainer;
