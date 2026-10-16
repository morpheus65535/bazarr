import { SelectorOption } from "@/components";

// Shared by the basic and enhanced languages profile editors.

export const subtitlesTypeOptions: SelectorOption<string>[] = [
  {
    label: "Normal or hearing-impaired",
    value: "normal",
  },
  {
    label: "Hearing-impaired required",
    value: "hi",
  },
  {
    label: "Non-HI only (exclude hearing-impaired)",
    value: "nonHi",
  },
  {
    label: "Forced (foreign part only)",
    value: "forced",
  },
];

export const inclusionOptions: SelectorOption<string>[] = [
  {
    label: "Always",
    value: "always_include",
  },
  {
    label: "audio track matches",
    value: "audioOnlyInclude",
  },
  {
    label: "no audio track matches",
    value: "audioExclude",
  },
];
