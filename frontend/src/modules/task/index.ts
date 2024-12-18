import {
  hideNotification,
  showNotification,
  updateNotification,
} from "@mantine/notifications";
import { uniqueId } from "lodash";
import { LOG } from "@/utilities/console";
import { notification } from "./notification";

class TaskDispatcher {
  private running: boolean;
  private tasks: Record<string, Task.Callable[]> = {};
  private progress: Record<string, boolean> = {};

  constructor() {
    this.running = false;
    this.tasks = {};
    this.progress = {};

    window.addEventListener("beforeunload", this.onBeforeUnload.bind(this));
  }

  private onBeforeUnload(e: BeforeUnloadEvent) {
    const message = "Background tasks are still running";

    if (Object.keys(this.tasks).length > 0) {
      e.preventDefault();
      e.returnValue = message;
      return;
    }
    delete e["returnValue"];
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

          const taskId = group;

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
              // TODO
            }
          }

          const notifyEnd = notification.progress.end(taskId, group);
          updateNotification(notifyEnd);

          delete this.tasks[group];
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
    // Clone this function
    const task = callable.bind({}) as Task.Callable<T>;
    task.parameters = parameters;
    task.description = name;
    task.id = uniqueId("task");

    if (this.tasks[group] === undefined) {
      this.tasks[group] = [];
      const notifyStart = notification.progress.pending(group, group);
      showNotification(notifyStart);
    }

    this.tasks[group].push(task);

    this.update();

    return task.id;
  }

  public updateProgress(items: Site.Progress[]) {
    items.forEach((item) => {
      if (this.progress[item.id] === undefined) {
        showNotification(notification.progress.pending(item.id, item.header));
        this.progress[item.id] = true;
        setTimeout(() => this.updateProgress([item]), 1000);

        return;
      }

      if (item.value >= item.count) {
        updateNotification(notification.progress.end(item.id, item.header));
        delete this.progress[item.id];

        return;
      }

      item.value += 1;

      updateNotification(
        notification.progress.update(
          item.id,
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
export * from "./group";
export * from "./notification";
