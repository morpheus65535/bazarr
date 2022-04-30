// A background task manager, use for dispatching task one by one
class TaskManager {
  private tasks: Task.Callable[] = [];
  constructor() {
    this.tasks = [];
    window.addEventListener("beforeunload", this.onBeforeUnload.bind(this));
  }

  private onBeforeUnload(e: BeforeUnloadEvent) {
    const message = "Background tasks are still running";

    if (this.tasks.some((t) => t.status === "running")) {
      e.preventDefault();
      e.returnValue = message;
      return;
    }
    delete e["returnValue"];
  }

  private findTask(ref: Task.TaskRef): Task.Callable | undefined {
    return this.tasks.find((t) => t.id === ref.callableId);
  }

  create<T extends Task.AnyCallable>(fn: T, parameters: Parameters<T>): symbol {
    // Clone this function
    const newTask = fn.bind({}) as Task.Callable<T>;
    newTask.status = "idle";
    newTask.parameters = parameters;
    newTask.id = Symbol(this.tasks.length);

    this.tasks.push(newTask);

    return newTask.id;
  }

  async run(taskRef: Task.TaskRef) {
    const task = this.findTask(taskRef);

    if (task === undefined) {
      throw new Error(`Task ${taskRef.name} not found`);
    }

    if (task.status !== "idle") {
      return;
    }

    task.status = "running";

    try {
      await task(...task.parameters);
      task.status = "success";
    } catch (err) {
      task.status = "failure";
      throw err;
    }
  }
}

const taskManager = new TaskManager();

export default taskManager;
