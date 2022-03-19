import { LOG } from "@/utilities/console";
import taskManager from ".";
import { GroupName } from "./group";

export function createTask<T extends Task.AnyCallable>(
  name: string,
  callable: T,
  ...parameters: Parameters<T>
): Task.TaskRef {
  const callableId = taskManager.create(callable, parameters);

  LOG("info", "task created", name);

  return {
    name,
    callableId,
  };
}

export function dispatchTask(tasks: Task.TaskRef[], group: GroupName) {
  setTimeout(async () => {
    for (const ref of tasks) {
      LOG("info", "dispatching task", ref.name);
      await taskManager.run(ref);
    }
  });
}

export function createAndDispatchTask<T extends Task.AnyCallable>(
  name: string,
  group: GroupName,
  callable: T,
  ...parameters: Parameters<T>
) {
  const task = createTask(name, callable, ...parameters);
  dispatchTask([task], group);
}
