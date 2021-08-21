import { keys } from "lodash";
import { siteAddProgress, siteRemoveProgress } from "../../@redux/actions";
import store from "../../@redux/store";

// A background task manager, use for dispatching task one by one
class BackgroundTask {
  private groups: Task.Group;
  constructor() {
    this.groups = {};
  }

  dispatch<T extends Task.Callable>(groupName: string, tasks: Task.Task<T>[]) {
    if (groupName in this.groups) {
      return false;
    }

    this.groups[groupName] = tasks;
    setTimeout(async () => {
      const dispatch = store.dispatch;

      for (let index = 0; index < tasks.length; index++) {
        const task = tasks[index];

        dispatch(
          siteAddProgress([
            {
              id: groupName,
              header: groupName,
              name: task.name,
              value: index,
              count: tasks.length,
            },
          ])
        );
        try {
          await task.callable(...task.parameters);
        } catch (error) {}
      }
      delete this.groups[groupName];
      dispatch(siteRemoveProgress([groupName]));
    });

    return true;
  }

  find(groupName: string, id: number) {
    if (groupName in this.groups) {
      return this.groups[groupName].find((v) => v.id === id) !== undefined;
    }
    return false;
  }

  has(groupName: string) {
    return groupName in this.groups;
  }

  isRunning() {
    return keys(this.groups).length > 0;
  }
}

export default new BackgroundTask();
