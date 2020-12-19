interface SystemStatusResult {
  bazarr_config_directory: string;
  bazarr_directory: string;
  bazarr_version: string;
  operating_system: string;
  python_version: string;
  radarr_version: string;
  sonarr_version: string;
}

interface SystemTaskResult {
  DT_RowId: string;
  interval: string;
  job_id: string;
  job_running: boolean;
  name: string;
  next_run_in: string;
  next_run_time: string;
}

interface SystemProvider {
  name: string;
  status: string;
  retry: string;
}

type SystemLogType = "INFO" | "WARNING" | "ERROR" | "DEBUG";

interface SystemLog {
  type: SystemLogType;
  timestamp: string;
  message: string;
}
