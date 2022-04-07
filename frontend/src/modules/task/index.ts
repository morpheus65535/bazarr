import { showNotification, updateNotification } from "@mantine/notifications";
import { notification } from "../notifications";
import TaskGroups, { GroupName } from "./group";

export function createTask<T extends Task.AnyCallable>(
  name: string,
  callable: T,
  ...parameters: Parameters<T>
): Task.Callable<T> {
  // Clone this function
  const task = callable.bind({}) as Task.Callable<T>;
  task.parameters = parameters;
  task.description = name;

  return task;
}

export function dispatchTask(tasks: Task.Callable[], group: GroupName) {
  setTimeout(async () => {
    const { description, notify } = TaskGroups[group];

    const notifyStart = notification.progress(
      group,
      notify,
      description,
      0,
      tasks.length
    );
    showNotification(notifyStart);

    for (let index = 0; index < tasks.length; index++) {
      const task = tasks[index];

      const notifyInProgress = notification.progress(
        group,
        notify,
        task.description,
        index,
        tasks.length
      );
      updateNotification(notifyInProgress);
      await task(...task.parameters);
    }

    const notifyEnd = notification.progress(
      group,
      notify,
      "All Tasks Completed",
      tasks.length,
      tasks.length
    );
    updateNotification(notifyEnd);
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
