import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { capitalize } from "lodash";
import React, { FunctionComponent, useCallback, useMemo } from "react";
import { Toast } from "react-bootstrap";
import { siteRemoveError } from "../../@redux/actions";
import { useReduxAction, useReduxStore } from "../../@redux/hooks/base";
import "./style.scss";

function useAlertList() {
  return useReduxStore((s) => s.site.alerts);
}

function useRemoveAlert() {
  return useReduxAction(siteRemoveError);
}

export interface AlertContainerProps {}

const AlertContainer: FunctionComponent<AlertContainerProps> = () => {
  const list = useAlertList();

  const alerts = useMemo(
    () =>
      list.map((v, idx) => <MessageHolder key={idx} {...v}></MessageHolder>),
    [list]
  );
  return (
    <div className="alert-container">
      <div className="toast-container">{alerts}</div>
    </div>
  );
};

type MessageHolderProps = ReduxStore.Error & {};

const MessageHolder: FunctionComponent<MessageHolderProps> = (props) => {
  const { message, id, type } = props;
  const removeAlert = useRemoveAlert();

  const remove = useCallback(() => removeAlert(id), [removeAlert, id]);

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

export default AlertContainer;
