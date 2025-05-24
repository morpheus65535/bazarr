import { uniqueId } from "lodash";
import { LOG } from "@/utilities/console";
import { notification, NotificationItem } from "./notification";

let notificationContextRef: {
  showNotification?: (notification: NotificationItem) => void;
  updateNotification?: (notification: NotificationItem) => void;
  hideNotification?: (id: string) => void;
  markAsReadFn?: () => void;
} = {};

export const setNotificationContextRef = (
  showFn: (notification: NotificationItem) => void,
  updateFn: (notification: NotificationItem) => void,
  hideFn: (id: string) => void,
  markAsReadFn: () => void,
) => {
  notificationContextRef = {
    showNotification: showFn,
    updateNotification: updateFn,
    hideNotification: hideFn,
    markAsReadFn: markAsReadFn,
  };
};

class TaskDispatcher {
  private running: boolean;
  private readonly tasks: Record<string, Task.Callable[]> = {};
  private readonly progress: Record<string, boolean> = {};
  private readonly taskNotificationIds: Record<string, string> = {};

  constructor() {
    this.running = false;
    this.tasks = {};
    this.progress = {};
    this.taskNotificationIds = {};

    window.addEventListener("beforeunload", this.onBeforeUnload.bind(this));
  }

  private onBeforeUnload(e: BeforeUnloadEvent) {
    const message = "Background tasks are still running";

    if (Object.keys(this.tasks).length > 0) {
      e.preventDefault();

      return message;
    }
  }

  private update() {
    if (this.running) {
      return;
    }

    LOG("info", "Starting background task queue");

    this.running = true;

    const queue = window.queueMicrotask?.bind(window) ?? setTimeout;

    queue(async () => {
      while (Object.keys(this.tasks).length > 0) {
        const groups = Object.keys(this.tasks);

        for await (const group of groups) {
          const tasks = this.tasks[group];

          // Use the stored notification ID that was created in the create method
          const taskId = this.taskNotificationIds[group];

          for (let index = 0; index < tasks.length; index++) {
            const task = tasks[index];

            const notifyInProgress = notification.progress.update(
              taskId,
              group,
              task.description,
              index,
              tasks.length,
            );

            updateNotification(notifyInProgress);

            try {
              await task(...task.parameters);
            } catch (error) {
              LOG("error", "Error while running task", task.description, error);
            }
          }

          const notifyEnd = notification.progress.end(taskId, group);

          updateNotification(notifyEnd);

          // Clear this group's tasks
          delete this.tasks[group];

          // Remove from progress tracking
          if (this.progress[taskId]) {
            delete this.progress[taskId];
          }

          // Clean up the notification ID tracking
          delete this.taskNotificationIds[group];
        }
      }

      this.running = false;
    });
  }

  public create<T extends Task.AnyCallable>(
    name: string,
    group: string,
    callable: T,
    ...parameters: Parameters<T>
  ): Task.Ref {
    const task = callable.bind({}) as Task.Callable<T>;
    task.parameters = parameters;
    task.description = name;

    task.id = uniqueId("task");

    if (this.tasks[group] === undefined) {
      this.tasks[group] = [];

      this.taskNotificationIds[group] = `${group}-${Date.now()}`;
    }

    this.tasks[group].push(task);

    this.update();

    return task.id;
  }

  public updateProgress(items: Site.Progress[]) {
    items.forEach((item) => {
      const notificationId = this.taskNotificationIds[item.header] || item.id;

      if (this.progress[notificationId] === undefined) {
        this.progress[notificationId] = true;
        return;
      }

      if (item.value >= item.count) {
        updateNotification(
          notification.progress.end(notificationId, item.header),
        );
        delete this.progress[notificationId];

        if (this.taskNotificationIds[item.header]) {
          delete this.taskNotificationIds[item.header];
          if (this.tasks[item.header]) {
            delete this.tasks[item.header];
          }
        }

        return;
      }

      item.value += 1;

      updateNotification(
        notification.progress.update(
          notificationId,
          item.header,
          item.name,
          item.value,
          item.count,
        ),
      );
    });
  }

  public removeProgress(ids: string[]) {
    setTimeout(
      () => ids.forEach((id) => hideNotification(id)),
      notification.PROGRESS_TIMEOUT,
    );
  }
}

export const task = new TaskDispatcher();

export const showNotification = (notification: NotificationItem) => {
  if (notificationContextRef.showNotification) {
    notificationContextRef.showNotification(notification);
  }
};

export const updateNotification = (notification: NotificationItem) => {
  if (notificationContextRef.updateNotification) {
    notificationContextRef.updateNotification(notification);
  }
};

export const hideNotification = (id: string) => {
  if (notificationContextRef.hideNotification) {
    notificationContextRef.hideNotification(id);
  }
};

export * from "./group";
export * from "./notification";
export * from "./hooks";
export * from "./NotificationContext";
