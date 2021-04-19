export const uiPageSizeKey = "storage-ui-pageSize";

export const storage: LocalStorageType = {
  get pageSize(): number {
    return parseInt(localStorage.getItem(uiPageSizeKey) ?? "50");
  },
  set pageSize(v: number) {
    localStorage.setItem(uiPageSizeKey, v.toString());
  },
};
