import BGT from "./";

export function useIsAnyTaskRunning() {
  return BGT.isRunning();
}

export function useIsAnyTaskRunningWithId(id: number) {
  return BGT.hasId(id);
}

export function useIsGroupTaskRunning(groupName: string) {
  return BGT.has(groupName);
}

export function useIsGroupTaskRunningWithId(groupName: string, id: number) {
  return BGT.find(groupName, id);
}
