import { FunctionComponent } from "react";
import { Tooltip } from "@mantine/core";
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
  let label = "Unknown";
  switch (action) {
    case HistoryAction.Delete:
      icon = faTrash;
      label = "Delete";
      break;
    case HistoryAction.Download:
      icon = faDownload;
      label = "Download";
      break;
    case HistoryAction.Manual:
      icon = faUser;
      label = "Manual";
      break;
    case HistoryAction.Sync:
      icon = faClock;
      label = "Sync";
      break;
    case HistoryAction.Upgrade:
      icon = faRecycle;
      label = "Upgrade";
      break;
    case HistoryAction.Upload:
      icon = faCloudUploadAlt;
      label = "Upload";
      break;
    case HistoryAction.Translated:
      icon = faLanguage;
      label = "Translated";
      break;
    default:
      icon = faClosedCaptioning;
      label = "Unknown";
      break;
  }

  if (icon) {
    return (
      <Tooltip
        label={label}
        openDelay={500}
        position="right"
        events={{ hover: true, focus: false, touch: true }}
      >
        <FontAwesomeIcon
          aria-label={label}
          title={title}
          icon={icon}
        ></FontAwesomeIcon>
      </Tooltip>
    );
  } else {
    return null;
  }
};

export default HistoryIcon;
