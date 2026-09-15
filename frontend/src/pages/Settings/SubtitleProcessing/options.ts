import { SelectorOption } from "@/components";
import { ProviderList } from "@/pages/Settings/Providers/list";

const buildColor = (name: string) => `color(name=${name})`;

export const colorOptions: SelectorOption<string>[] = [
  {
    label: "White",
    value: buildColor("white"),
  },
  {
    label: "Light Gray",
    value: buildColor("light-gray"),
  },
  {
    label: "Red",
    value: buildColor("red"),
  },
  {
    label: "Green",
    value: buildColor("green"),
  },
  {
    label: "Yellow",
    value: buildColor("yellow"),
  },
  {
    label: "Blue",
    value: buildColor("blue"),
  },
  {
    label: "Magenta",
    value: buildColor("magenta"),
  },
  {
    label: "Cyan",
    value: buildColor("cyan"),
  },
  {
    label: "Black",
    value: buildColor("black"),
  },
  {
    label: "Dark Red",
    value: buildColor("dark-red"),
  },
  {
    label: "Dark Green",
    value: buildColor("dark-green"),
  },
  {
    label: "Dark Yellow",
    value: buildColor("dark-yellow"),
  },
  {
    label: "Dark Blue",
    value: buildColor("dark-blue"),
  },
  {
    label: "Dark Magenta",
    value: buildColor("dark-magenta"),
  },
  {
    label: "Dark Cyan",
    value: buildColor("dark-cyan"),
  },
  {
    label: "Dark Grey",
    value: buildColor("dark-grey"),
  },
];

export const providerOptions: SelectorOption<string>[] = ProviderList.map(
  (v) => ({
    label: v.key,
    value: v.key,
  }),
);

export const syncMaxOffsetSecondsOptions: SelectorOption<number>[] = [
  {
    label: "60",
    value: 60,
  },
  {
    label: "120",
    value: 120,
  },
  {
    label: "300",
    value: 300,
  },
  {
    label: "600",
    value: 600,
  },
];

export const forceAudioOption: SelectorOption<string>[] = [
  {
    label: "Use Audio Track as Reference",
    value: "true",
  },
  {
    label: "Use Embedded Subtitles as Reference",
    value: "false",
  },
];
