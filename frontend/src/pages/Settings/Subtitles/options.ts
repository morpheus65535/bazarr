import { SelectorOption } from "@/components";

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
