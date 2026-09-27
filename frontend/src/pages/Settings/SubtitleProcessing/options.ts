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

export const qualityMinScoreOptions: SelectorOption<number>[] = [
  {
    label: "0.0 (Accept all results)",
    value: 0.0,
  },
  {
    label: "0.1",
    value: 0.1,
  },
  {
    label: "0.2",
    value: 0.2,
  },
  {
    label: "0.3",
    value: 0.3,
  },
  {
    label: "0.4",
    value: 0.4,
  },
  {
    label: "0.5 (Moderate)",
    value: 0.5,
  },
  {
    label: "0.6",
    value: 0.6,
  },
  {
    label: "0.7",
    value: 0.7,
  },
  {
    label: "0.8",
    value: 0.8,
  },
  {
    label: "0.9",
    value: 0.9,
  },
  {
    label: "1.0 (Strict)",
    value: 1.0,
  },
];

export const qualityMaxOffsetSecondsOptions: SelectorOption<number>[] = [
  {
    label: "5 seconds",
    value: 5,
  },
  {
    label: "10 seconds",
    value: 10,
  },
  {
    label: "15 seconds",
    value: 15,
  },
  {
    label: "20 seconds",
    value: 20,
  },
  {
    label: "30 seconds",
    value: 30,
  },
  {
    label: "45 seconds",
    value: 45,
  },
  {
    label: "60 seconds",
    value: 60,
  },
];

export const qualityMaxFramerateDeviationOptions: SelectorOption<number>[] = [
  {
    label: "0.05 (5%)",
    value: 0.05,
  },
  {
    label: "0.1 (10%)",
    value: 0.1,
  },
  {
    label: "0.15 (15%)",
    value: 0.15,
  },
  {
    label: "0.2 (20%)",
    value: 0.2,
  },
  {
    label: "0.3 (30%)",
    value: 0.3,
  },
];
