declare namespace System {
  interface Announcements {
    text: string;
    link: string;
    hash: string;
    dismissible: boolean;
    timestamp: string;
  }

  interface Task {
    interval: string;
    job_id: string;
    job_running: boolean;
    name: string;
    next_run_in: string;
    next_run_time: string;
  }

  interface Jobs {
    job_id: number;
    job_name: string;
    status: string;
    last_run_time: string;
    is_progress: boolean;
    progress_value: number;
    progress_max: number;
    progress_message: string;
  }

  interface Status {
    bazarr_config_directory: string;
    bazarr_directory: string;
    bazarr_version: string;
    database_engine: string;
    database_migration: string;
    operating_system: string;
    package_version: string;
    python_version: string;
    radarr_version: string;
    sonarr_version: string;
    start_time: number;
    timezone: string;
  }

  interface Backups {
    type: string;
    filename: string;
    size: string;
    date: string;
    id: number;
  }

  interface Health {
    object: string;
    issue: string;
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
