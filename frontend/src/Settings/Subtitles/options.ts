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

export const antiCaptchaOption: SelectorOption<string>[] = [
  {
    label: "Anti-Captcha",
    value: "anti-captcha",
  },
  {
    label: "Death by Captcha",
    value: "death-by-captcha",
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
