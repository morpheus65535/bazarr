import { keys } from "lodash";
import {
  siteAddProgress,
  siteRemoveProgress,
  siteUpdateProgressCount,
} from "../../@redux/actions";
import store from "../../@redux/store";

// A background task manager, use for dispatching task one by one
class BackgroundTask {
  private groups: Task.Group;
  constructor() {
    this.groups = {};
  }

  dispatch<T extends Task.Callable>(groupName: string, tasks: Task.Task<T>[]) {
    if (groupName in this.groups) {
      this.groups[groupName].push(...tasks);
      store.dispatch(
        siteUpdateProgressCount({
          id: groupName,
          count: this.groups[groupName].length,
        })
      );
      return;
    }

    this.groups[groupName] = tasks;
    setTimeout(async () => {
      for (let index = 0; index < tasks.length; index++) {
        const task = tasks[index];

        store.dispatch(
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
      store.dispatch(siteRemoveProgress([groupName]));
    });
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

  hasId(id: number) {
    for (const key in this.groups) {
      const tasks = this.groups[key];
      if (tasks.find((v) => v.id === id) !== undefined) {
        return true;
      }
    }
    return false;
  }

  isRunning() {
    return keys(this.groups).length > 0;
  }
}

export default new BackgroundTask();
