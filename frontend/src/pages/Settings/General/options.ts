import { SelectorOption } from "@/components";

export const securityOptions: SelectorOption<string>[] = [
  {
    label: "Basic",
    value: "basic",
  },
  {
    label: "Form",
    value: "form",
  },
];

export const proxyOptions: SelectorOption<string>[] = [
  {
    label: "Socks5 (local DNS)",
    value: "socks5",
  },
  {
    label: "Socks5h (remote DNS)",
    value: "socks5h",
  },
  {
    label: "HTTP(S)",
    value: "http",
  },
];

export const branchOptions: SelectorOption<string>[] = [
  {
    label: "master",
    value: "master",
  },
  {
    label: "development",
    value: "development",
  },
];
