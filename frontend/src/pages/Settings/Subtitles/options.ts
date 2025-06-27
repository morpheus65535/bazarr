import { SelectorOption } from "@/components";
import { ProviderList } from "@/pages/Settings/Providers/list";

export const hiExtensionOptions: SelectorOption<string>[] = [
  {
    label: ".hi (Hearing-Impaired)",
    value: "hi",
  },
  {
    label: ".sdh (Subtitles for the Deaf or Hard-of-Hearing)",
    value: "sdh",
  },
  {
    label: ".cc (Close Captioned)",
    value: "cc",
  },
];

export const folderOptions: SelectorOption<string>[] = [
  {
    label: "AlongSide Media File",
    value: "current",
  },
  {
    label: "Relative Path to Media File",
    value: "relative",
  },
  {
    label: "Absolute Path",
    value: "absolute",
  },
];

export const embeddedSubtitlesParserOption: SelectorOption<string>[] = [
  {
    label:
      "ffprobe (faster than mediainfo. Part of Bazarr installation already)",
    value: "ffprobe",
  },
  {
    label:
      "mediainfo (slower but may give better results. User must install the mediainfo executable first)",
    value: "mediainfo",
  },
];

export const adaptiveSearchingDelayOption: SelectorOption<string>[] = [
  {
    label: "1 week",
    value: "1w",
  },
  {
    label: "2 weeks",
    value: "2w",
  },
  {
    label: "3 weeks",
    value: "3w",
  },
  {
    label: "4 weeks",
    value: "4w",
  },
];

export const adaptiveSearchingDeltaOption: SelectorOption<string>[] = [
  {
    label: "3 days",
    value: "3d",
  },
  {
    label: "1 week",
    value: "1w",
  },
  {
    label: "2 weeks",
    value: "2w",
  },
  {
    label: "3 weeks",
    value: "3w",
  },
  {
    label: "4 weeks",
    value: "4w",
  },
];

function buildColor(name: string) {
  return `color(name=${name})`;
}

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

export const translatorOption: SelectorOption<string>[] = [
  {
    label: "Google Translate",
    value: "google_translate",
  },
  {
    label: "Gemini",
    value: "gemini",
  },
  {
    label: "Lingarr",
    value: "lingarr",
  },
];
