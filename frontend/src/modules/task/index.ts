// A background task manager, use for dispatching task one by one
class TaskManager {
  private tasks: Task.Callable[] = [];
  constructor() {
    this.tasks = [];
    window.addEventListener("beforeunload", this.onBeforeUnload.bind(this));
  }

  private onBeforeUnload(e: BeforeUnloadEvent) {
    const message = "Background tasks are still running";

    if (this.tasks.some((t) => t.status !== "success")) {
      e.preventDefault();
      e.returnValue = message;
      return;
    }
    delete e["returnValue"];
  }

  private generateUniqueId(): string {
    return "TODO-TODO";
  }

  create<T extends Task.AnyCallable>(fn: T, parameters: Parameters<T>): string {
    const newTask = fn as Task.Callable<T>;
    newTask.status = "idle";
    newTask.parameters = parameters;
    newTask.id = this.generateUniqueId();

    this.tasks.push(newTask);

    return newTask.id;
  }

  async run(task: Task.Callable) {
    if (task.status !== "idle") {
      return;
    }

    task.status = "running";

    try {
      await task(...task.parameters);
      task.status = "success";
    } catch (err) {
      task.status = "failure";
    }
  }
}

const taskManager = new TaskManager();

export default taskManager;
