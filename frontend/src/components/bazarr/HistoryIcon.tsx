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
import { IconDefinition } from "@fortawesome/fontawesome-svg-core";

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
  const actionMap: Record<number, { icon: IconDefinition; label: string }> = {
    [HistoryAction.Delete]: { icon: faTrash, label: "Delete" },
    [HistoryAction.Download]: { icon: faDownload, label: "Download" },
    [HistoryAction.Manual]: { icon: faUser, label: "Manual" },
    [HistoryAction.Sync]: { icon: faClock, label: "Sync" },
    [HistoryAction.Upgrade]: { icon: faRecycle, label: "Upgrade" },
    [HistoryAction.Upload]: { icon: faCloudUploadAlt, label: "Upload" },
    [HistoryAction.Translated]: { icon: faLanguage, label: "Translated" },
  };
  const { icon = faClosedCaptioning, label = "Unknown" } =
    actionMap[action] ?? {};

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
