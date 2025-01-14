import { SelectorOption } from "@/components";

export const pageSizeOptions: SelectorOption<number>[] = [
  {
    label: "25",
    value: 25,
  },
  {
    label: "50",
    value: 50,
  },
  {
    label: "100",
    value: 100,
  },
  {
    label: "250",
    value: 250,
  },
  {
    label: "500",
    value: 500,
  },
  {
    label: "1000",
    value: 1000,
  },
];

export const colorSchemeOptions: SelectorOption<string>[] = [
  {
    label: "Auto",
    value: "auto",
  },
  {
    label: "Light",
    value: "light",
  },
  {
    label: "Dark",
    value: "dark",
  },
];
