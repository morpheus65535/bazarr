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
    value: buildColor("lightgray"),
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
    value: buildColor("darkred"),
  },
  {
    label: "Dark Green",
    value: buildColor("darkgreen"),
  },
  {
    label: "Dark Yellow",
    value: buildColor("darkyellow"),
  },
  {
    label: "Dark Blue",
    value: buildColor("darkblue"),
  },
  {
    label: "Dark Magenta",
    value: buildColor("darkmagenta"),
  },
  {
    label: "Dark Cyan",
    value: buildColor("darkcyan"),
  },
  {
    label: "Dark Grey",
    value: buildColor("darkgrey"),
  },
];
