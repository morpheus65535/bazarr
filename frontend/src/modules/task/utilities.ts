import { LOG } from "@/utilities/console";
import taskManager from ".";
import { siteAddProgress, siteRemoveProgress } from "../redux/actions";
import store from "../redux/store";
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
    for (let index = 0; index < tasks.length; index++) {
      const ref = tasks[index];
      LOG("info", "dispatching task", ref.name);

      store.dispatch(
        siteAddProgress([
          {
            id: group,
            header: group,
            name: ref.name,
            value: index,
            count: tasks.length,
          },
        ])
      );

      await taskManager.run(ref);
    }

    // TODO: Also remove from taskManager
    store.dispatch(siteRemoveProgress([group]));
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
