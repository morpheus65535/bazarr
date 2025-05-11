import { SelectorOption } from "@/components";

export const seriesSyncOptions: SelectorOption<number>[] = [
  { label: "Manually", value: 52560000 },
  { label: "15 Minutes", value: 15 },
  { label: "1 Hour", value: 60 },
  { label: "3 Hours", value: 180 },
  { label: "6 Hours", value: 360 },
  { label: "12 Hours", value: 720 },
  { label: "24 Hours", value: 1440 },
  { label: "Weekly", value: 10080 },
];

export const moviesSyncOptions = seriesSyncOptions;

export const diskUpdateOptions: SelectorOption<string>[] = [
  { label: "Manually", value: "Manually" },
  { label: "Daily", value: "Daily" },
  { label: "Weekly", value: "Weekly" },
];

export const backupOptions = diskUpdateOptions;

export const dayOptions: SelectorOption<number>[] = [
  { label: "Monday", value: 0 },
  { label: "Tuesday", value: 1 },
  { label: "Wednesday", value: 2 },
  { label: "Thursday", value: 3 },
  { label: "Friday", value: 4 },
  { label: "Saturday", value: 5 },
  { label: "Sunday", value: 6 },
];

export const upgradeOptions: SelectorOption<number>[] = [
  { label: "Manually", value: 876000 },
  { label: "6 Hours", value: 6 },
  { label: "12 Hours", value: 12 },
  { label: "24 Hours", value: 24 },
  { label: "Weekly", value: 168 },
];
