import { uniqueId } from "lodash";
import { LOG } from "@/utilities/console";

class TaskDispatcher {
  private running: boolean;
  private tasks: Record<string, Task.Callable[]> = {};

  constructor() {
    this.running = false;
    this.tasks = {};

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

          for (let index = 0; index < tasks.length; index++) {
            const task = tasks[index];

            try {
              await task(...task.parameters);
            } catch (error) {
              // TODO
            }
          }

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
    }

    this.tasks[group].push(task);

    this.update();

    return task.id;
  }
}

export const task = new TaskDispatcher();
export * from "./group";
export * from "./notification";
