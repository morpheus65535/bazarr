import { ReactText } from "react";

type AvailableType = ReactText | boolean;
export interface ProviderInfo {
  key: string;
  name?: string;
  description?: string;
  message?: string;
  defaultKey?: {
    [key: string]: AvailableType;
  };
  keyNameOverride?: {
    [key: string]: string;
  };
}

export const ProviderList: Readonly<ProviderInfo[]> = [
  {
    key: "addic7ed",
    description: "Requires Anti-Captcha Provider",
    defaultKey: {
      username: "",
      password: "",
    },
  },
  { key: "argenteam", description: "Spanish Subtitles Provider" },
  {
    key: "assrt",
    description: "Chinese Subtitles Provider",
    defaultKey: {
      token: "",
    },
  },
  {
    key: "betaseries",
    name: "BetaSeries",
    description: "French / English Provider for TV Shows Only",
    defaultKey: {
      token: "",
    },
    keyNameOverride: {
      token: "API KEY",
    },
  },
  {
    key: "bsplayer",
    name: "BSplayer",
  },
  {
    key: "greeksubs",
    name: "GreekSubs",
    description: "Greek Subtitles Provider",
  },
  {
    key: "greeksubtitles",
    name: "GreekSubtitles",
    description: "Greek Subtitles Provider",
  },
  { key: "hosszupuska", description: "Hungarian Subtitles Provider" },
  {
    key: "legendasdivx",
    name: "LegendasDivx",
    description: "Brazilian / Portuguese Subtitles Provider",
    defaultKey: {
      username: "",
      password: "",
      skip_wrong_fps: false,
    },
    keyNameOverride: {
      skip_wrong_fps: "Skip Wrong FPS",
    },
  },
  {
    key: "legendastv",
    name: "LegendasTV",
    description: "Brazilian / Portuguese Subtitles Provider",
    defaultKey: {
      username: "",
      password: "",
    },
  },
  { key: "napiprojekt", description: "Polish Subtitles Provider" },
  {
    key: "napisy24",
    description: "Polish Subtitles Provider",
    message:
      "The provided credentials must have API access. Leave empty to use the defaults.",
    defaultKey: {
      username: "",
      password: "",
    },
  },
  { key: "nekur", description: "Latvian Subtitles Provider" },
  {
    key: "opensubtitles",
    name: "OpenSubtitles.org",
    defaultKey: {
      username: "",
      password: "",
      vip: false,
      ssl: false,
      skip_wrong_fps: false,
    },
    keyNameOverride: {
      vip: "VIP",
      ssl: "Use SSL",
      skip_wrong_fps: "Skip Wrong FPS",
    },
  },
  {
    key: "opensubtitlescom",
    name: "OpenSubtitles.com",
    defaultKey: {
      username: "",
      password: "",
      use_hash: false,
    },
    keyNameOverride: {
      use_hash: "Use Hash",
    },
  },
  { key: "podnapisi" },
  {
    key: "regielive",
    name: "RegieLive",
    description: "Romanian Subtitles Provider",
  },
  {
    key: "soustitres",
    name: "Sous-Titres.eu",
    description: "Mostly French Subtitles Provider",
  },
  { key: "subdivx", description: "Spanish Subtitles Provider" },
  {
    key: "subssabbz",
    name: "Subs.sab.bz",
    description: "Bulgarian Subtitles Provider",
  },
  {
    key: "subs4free",
    name: "Subs4Free",
    description: "Greek Subtitles Provider",
  },
  {
    key: "subs4series",
    name: "Subs4Series",
    description: "Greek Subtitles Provider",
  },
  {
    key: "subscene",
    description: "Requires Anti-Captcha Provider",
    defaultKey: {
      username: "",
      password: "",
    },
  },
  { key: "subscenter" },
  {
    key: "subsunacs",
    name: "Subsunacs.net",
    description: "Bulgarian Subtitles Provider",
  },
  { key: "subsynchro", description: "French Subtitles Provider" },
  {
    key: "subtitri",
    name: "subtitri.id.lv",
    description: "Latvian Subtitles Provider",
  },
  {
    key: "subtitulamos",
    name: "Subtitulamos.tv",
    description: "Spanish Subtitles Provider",
  },
  { key: "sucha", description: "Spanish Subtitles Provider" },
  { key: "supersubtitles" },
  {
    key: "titlovi",
    defaultKey: {
      username: "",
      password: "",
    },
  },
  { key: "titrari", name: "Titrari.ro" },
  {
    key: "tusubtitulo",
    name: "Tusubtitulo.com",
    description: "Spanish / English Subtitles Provider for TV Shows",
  },
  { key: "tvsubtitles", name: "TVSubtitles" },
  { key: "wizdom", description: "Wizdom.xyz Subtitles Provider." },
  {
    key: "xsubs",
    name: "XSubs",
    description: "Greek Subtitles Provider",
    defaultKey: {
      username: "",
      password: "",
    },
  },
  {
    key: "yavka",
    name: "Yavka.net",
    description: "Bulgarian Subtitles Provider",
  },
  { key: "yify", name: "YIFY Subtitles" },
  { key: "zimuku", description: "Chinese Subtitles Provider" },
];
