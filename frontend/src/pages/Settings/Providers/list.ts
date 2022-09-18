import { ReactText } from "react";

type Input<T, N> = {
  type: N;
  key: string;
  defaultValue?: T;
  name?: string;
  description?: string;
};

type AvailableInput =
  | Input<ReactText, "text">
  | Input<string, "password">
  | Input<boolean, "switch">
  | Input<ReactText[], "chips">;

export interface ProviderInfo {
  key: string;
  name?: string;
  description?: string;
  message?: string;
  inputs?: AvailableInput[];
}

export const ProviderList: Readonly<ProviderInfo[]> = [
  {
    key: "addic7ed",
    description: "Requires Anti-Captcha Provider or cookies",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
      {
        type: "text",
        key: "cookies",
        name: "Cookies, e.g., PHPSESSID=abc; wikisubtitlesuser=xyz; wikisubtitlespass=efg",
      },
      {
        type: "text",
        key: "user_agent",
        name: "User-Agent, e.g., Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
      },
      {
        type: "switch",
        key: "vip",
        name: "VIP",
      },
    ],
  },
  { key: "argenteam", description: "LATAM Spanish Subtitles Provider" },
  {
    key: "assrt",
    description: "Chinese Subtitles Provider",
    inputs: [
      {
        type: "text",
        key: "token",
      },
    ],
  },
  {
    key: "betaseries",
    name: "BetaSeries",
    description: "French / English Provider for TV Shows Only",
    inputs: [
      {
        type: "text",
        key: "token",
        name: "API KEY",
      },
    ],
  },
  {
    key: "bsplayer",
    name: "BSplayer",
    description:
      "Provider removed from Bazarr because it was causing too much issues so it will always return no subtitles",
  },
  {
    key: "embeddedsubtitles",
    name: "Embedded Subtitles",
    description: "Embedded Subtitles from your Media Files",
    inputs: [
      {
        type: "chips",
        key: "included_codecs",
        name: "Allowed codecs (subrip, ass, webvtt, mov_text). Leave empty to allow all.",
        defaultValue: [],
      },
      {
        type: "text",
        key: "timeout",
        defaultValue: 600,
        name: "Extraction timeout in seconds",
      },
      {
        type: "switch",
        key: "hi_fallback",
        name: "Use HI subtitles as a fallback (don't enable this if you have a HI language profile)",
      },
      {
        type: "switch",
        key: "unknown_as_english",
        name: "Use subtitles with unknown info/language as english",
      },
    ],
    message:
      "Warning for cloud users: this provider needs to read the entire file in order to extract subtitles.",
  },
  {
    key: "gestdown",
    name: "Gestdown (Addic7ed proxy)",
    description: "Proxy for Addic7ed website. No need for login or cookies.",
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
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
      { type: "switch", key: "skip_wrong_fps", name: "Skip Wrong FPS" },
    ],
  },
  {
    key: "karagarga",
    name: "Karagarga.in",
    description: "Movie Subtitles Provider (Private Tracker)",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
      {
        type: "text",
        key: "f_username",
        name: "Forum username",
      },
      {
        type: "password",
        key: "f_password",
        name: "Forum password",
      },
    ],
  },
  {
    key: "ktuvit",
    name: "Ktuvit",
    description: "Hebrew Subtitles Provider",
    inputs: [
      {
        type: "text",
        key: "email",
      },
      {
        type: "text",
        key: "hashed_password",
        name: "Hashed Password",
      },
    ],
  },
  {
    key: "legendastv",
    name: "LegendasTV",
    description: "Brazilian / Portuguese Subtitles Provider",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
      {
        type: "switch",
        key: "featured_only",
        name: "Only Download Featured",
      },
    ],
  },
  { key: "napiprojekt", description: "Polish Subtitles Provider" },
  {
    key: "napisy24",
    description: "Polish Subtitles Provider",
    message:
      "The provided credentials must have API access. Leave empty to use the defaults.",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
    ],
  },
  { key: "nekur", description: "Latvian Subtitles Provider" },
  {
    key: "opensubtitles",
    name: "OpenSubtitles.org",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
      {
        type: "switch",
        key: "vip",
        name: "VIP",
      },
      {
        type: "switch",
        key: "ssl",
        name: "Use SSL",
      },
      {
        type: "switch",
        key: "skip_wrong_fps",
        name: "Skip Wrong FPS",
      },
    ],
  },
  {
    key: "opensubtitlescom",
    name: "OpenSubtitles.com",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
      {
        type: "switch",
        key: "use_hash",
        name: "Use Hash",
      },
    ],
  },
  {
    key: "podnapisi",
    name: "Podnapisi",
    inputs: [
      {
        type: "switch",
        key: "verify_ssl",
        name: "Verify SSL certificate (disabling this introduces a MitM attack risk)",
        defaultValue: true,
      },
    ],
  },
  {
    key: "regielive",
    name: "RegieLive",
    description: "Romanian Subtitles Provider. Broken, will not works.",
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
    key: "subf2m",
    name: "subf2m.co",
    description: "Subscene Alternative Provider",
  },
  {
    key: "subs4free",
    name: "Subs4Free",
    description: "Greek Subtitles Provider. Broken, may not works for some.",
  },
  {
    key: "subs4series",
    name: "Subs4Series",
    description:
      "Greek Subtitles Provider. Requires anti-captcha provider to solve captchas for each download.",
  },
  {
    key: "subscene",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
    ],
    description: "Broken, may not works for some. Use subf2m instead.",
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
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
    ],
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
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
      {
        type: "switch",
        key: "approved_only",
        name: "Skip unapproved subtitles",
      },
    ],
  },
  { key: "tvsubtitles", name: "TVSubtitles" },
  { key: "wizdom", description: "Wizdom.xyz Subtitles Provider." },
  {
    key: "xsubs",
    name: "XSubs",
    description: "Greek Subtitles Provider",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "password",
      },
    ],
  },
  {
    key: "yavkanet",
    name: "Yavka.net",
    description: "Bulgarian Subtitles Provider",
  },
  { key: "yifysubtitles", name: "YIFY Subtitles" },
  { key: "zimuku", description: "Chinese Subtitles Provider" },
];
