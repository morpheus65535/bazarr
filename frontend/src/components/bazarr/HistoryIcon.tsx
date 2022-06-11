import {
  faClock,
  faClosedCaptioning,
  faCloudUploadAlt,
  faDownload,
  faLanguage,
  faRecycle,
  faTrash,
  faUser,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { FunctionComponent } from "react";

enum HistoryAction {
  Delete = 0,
  Download,
  Manual,
  Upgrade,
  Upload,
  Sync,
  Translated,
}

const HistoryIcon: FunctionComponent<{
  action: number;
  title?: string;
}> = ({ action, title }) => {
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
    case HistoryAction.Translated:
      icon = faLanguage;
      break;
    default:
      icon = faClosedCaptioning;
      break;
  }

  if (icon) {
    return <FontAwesomeIcon title={title} icon={icon}></FontAwesomeIcon>;
  } else {
    return null;
  }
};

export default HistoryIcon;
