namespace System {
  interface Task {
    interval: string;
    job_id: string;
    job_running: boolean;
    name: string;
    next_run_in: string;
    next_run_time: string;
  }

  interface Status {
    bazarr_config_directory: string;
    bazarr_directory: string;
    bazarr_version: string;
    operating_system: string;
    python_version: string;
    radarr_version: string;
    sonarr_version: string;
  }

  interface Provider {
    name: string;
    status: string;
    retry: string;
  }

  type LogType = "INFO" | "WARNING" | "ERROR" | "DEBUG";

  interface Log {
    type: System.LogType;
    timestamp: string;
    message: string;
    exception?: string;
  }
}
