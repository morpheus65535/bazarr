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
    description: "Requires Anti-Captcha Provider or cookies",
    defaultKey: {
      username: "",
      password: "",
      cookies: "",
      user_agent: "",
      vip: false,
    },
    keyNameOverride: {
      vip: "VIP",
      cookies:
        "Cookies, e.g., PHPSESSID=abc; wikisubtitlesuser=xyz; wikisubtitlespass=efg",
      user_agent:
        "User-Agent, e.g., Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
    },
  },
  { key: "argenteam", description: "LATAM Spanish Subtitles Provider" },
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
    key: "embeddedsubtitles",
    name: "Embedded Subtitles",
    description: "Embedded Subtitles from your Media Files",
    defaultKey: {
      include_srt: true,
      include_ass: true,
      hi_fallback: false,
    },
    message:
      "Warning for cloud users: this provider needs to read the entire file in order to extract subtitles.",
    keyNameOverride: {
      include_srt: "Include SRT",
      include_ass: "Include ASS (will be converted to SRT)",
      hi_fallback:
        "Use HI subtitles as a fallback (don't enable it if you have a HI language profile)",
    },
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
    key: "ktuvit",
    name: "Ktuvit",
    description: "Hebrew Subtitles Provider",
    defaultKey: {
      email: "",
      hashed_password: "",
    },
    keyNameOverride: {
      hashed_password: "Hashed Password",
    },
  },
  {
    key: "legendastv",
    name: "LegendasTV",
    description: "Brazilian / Portuguese Subtitles Provider",
    defaultKey: {
      username: "",
      password: "",
      featured_only: false,
    },
    keyNameOverride: {
      featured_only: "Only Download Featured",
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
  {
    key: "podnapisi",
    name: "Podnapisi",
    defaultKey: {
      verify_ssl: true,
    },
    keyNameOverride: {
      verify_ssl:
        "Verify SSL certificate (disabling introduce a MitM attack risk)",
    },
  },
  {
    key: "regielive",
    name: "RegieLive",
    description: "Romanian Subtitles Provider",
  },
  {
    key: "soustitreseu",
    name: "Sous-Titres.eu",
    description: "Mostly French Subtitles Provider",
  },
  { key: "subdivx", description: "LATAM Spanish / Spanish Subtitles Provider" },
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
    description:
      "Greek Subtitles Provider. Require anti-captcha provider to solve on each download.",
  },
  {
    key: "subscene",
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
    key: "subtitrarinoi",
    name: "Subtitrari-noi.ro",
    description: "Romanian Subtitles Provider",
  },
  {
    key: "subtitriid",
    name: "subtitri.id.lv",
    description: "Latvian Subtitles Provider",
  },
  {
    key: "subtitulamostv",
    name: "Subtitulamos.tv",
    description: "Spanish Subtitles Provider",
  },
  { key: "sucha", description: "LATAM Spanish Subtitles Provider" },
  { key: "supersubtitles" },
  {
    key: "titlovi",
    defaultKey: {
      username: "",
      password: "",
    },
  },
  {
    key: "titrari",
    name: "Titrari.ro",
    description: "Mostly Romanian Subtitles Provider",
  },
  {
    key: "tusubtitulo",
    name: "Tusubtitulo.com",
    description:
      "Provider requested to be removed from Bazarr so it will always return no subtitles. Could potentially come back in the future with an upcoming premium account.",
    // "LATAM Spanish / Spanish / English Subtitles Provider for TV Shows",
  },
  {
    key: "titulky",
    name: "Titulky.com",
    description: "CZ/SK Subtitles Provider. Available only with VIP",
    defaultKey: {
      username: "",
      password: "",
      skip_wrong_fps: false,
      approved_only: false,
      multithreading: true,
    },
    keyNameOverride: {
      skip_wrong_fps: "Skip mismatching FPS",
      approved_only: "Skip unapproved subtitles",
      multithreading: "Enable multithreading",
    },
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
    key: "yavkanet",
    name: "Yavka.net",
    description: "Bulgarian Subtitles Provider",
  },
  { key: "yifysubtitles", name: "YIFY Subtitles" },
  { key: "zimuku", description: "Chinese Subtitles Provider" },
];
