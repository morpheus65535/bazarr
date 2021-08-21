import BGT from "./";

export function useIsAnyTaskRunning() {
  return BGT.isRunning();
}

export function useIsGroupTaskRunning(groupName: string) {
  return BGT.has(groupName);
}

export function useIsIdRunning(groupName: string, id: number) {
  return BGT.find(groupName, id);
}
