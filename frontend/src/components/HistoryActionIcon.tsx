import React, { FunctionComponent } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faTrash,
  faDownload,
  faUser,
  faRecycle,
  faCloudUploadAlt,
  faClock,
} from "@fortawesome/free-solid-svg-icons";

interface HistoryActionIconProps {
  action: number;
}

enum HistoryAction {
  Delete = 0,
  Download,
  Manual,
  Upgrade,
  Upload,
  Sync,
}

const HistoryActionIcon: FunctionComponent<HistoryActionIconProps> = (
  props
) => {
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

export default HistoryActionIcon;
