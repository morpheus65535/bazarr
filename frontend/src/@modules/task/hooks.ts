import BGT from "./";

export function useIsAnyTaskRunning() {
  return BGT.isRunning();
}

export function useIsAnyTaskRunningWithId(ids: number[]) {
  return BGT.hasId(ids);
}

export function useIsGroupTaskRunning(groupName: string) {
  return BGT.has(groupName);
}

export function useIsGroupTaskRunningWithId(groupName: string, id: number) {
  return BGT.find(groupName, id);
}
