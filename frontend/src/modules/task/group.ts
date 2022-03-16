export type GroupName =
  | "scan-disk"
  | "search-subtitles"
  | "download-subtitles"
  | "upload-subtitles"
  | "modify-subtitles";

type TaskGroup = {
  [key in GroupName]: Task.Group;
};

const TaskGroups: TaskGroup = {
  "scan-disk": {
    description: "Scanning Disk...",
    notify: "Scanning...",
  },
  "search-subtitles": {
    description: "Searching Subtitles...",
    notify: "Searching...",
  },
  "download-subtitles": {
    description: "Downloading Subtitles...",
    notify: "Downloading...",
  },
  "upload-subtitles": {
    description: "Uploading Subtitles...",
    notify: "Uploading...",
  },
  "modify-subtitles": {
    description: "Modifying Subtitles...",
    notify: "Modifying...",
  },
};

export default TaskGroups;
