import { SelectorOption } from "@/components";

type Text = string | number;

type Input<T, N> = {
  type: N;
  key: string;
  defaultValue?: T;
  name?: string;
  description?: string;
  options?: SelectorOption<string>[];
  validation?: {
    rule: (value: string) => string | null;
  };
};

type AvailableInput =
  | Input<Text, "text">
  | Input<string, "password">
  | Input<boolean, "switch">
  | Input<string, "select">
  | Input<string, "testbutton">
  | Input<Text[], "chips">;

export interface ProviderInfo {
  key: string;
  name?: string;
  description?: string;
  message?: string;
  inputs?: AvailableInput[];
}

export const logLevelOptions: SelectorOption<string>[] = [
  { label: "DEBUG", value: "DEBUG" },
  { label: "INFO", value: "INFO" },
  { label: "WARNING", value: "WARNING" },
  { label: "ERROR", value: "ERROR" },
  { label: "CRITICAL", value: "CRITICAL" },
];

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
  {
    key: "animekalesi",
    name: "AnimeKalesi",
    description: "Turkish Anime Series Subtitles Provider",
  },
  {
    key: "animetosho",
    name: "Anime Tosho",
    description:
      "Anime Tosho is a free, completely automated service which mirrors most torrents posted on TokyoTosho's anime category, Nyaa.si's English translated anime category and AniDex's anime category.",
    inputs: [
      {
        type: "text",
        key: "search_threshold",
        defaultValue: 6,
        name: "Search Threshold. Increase if you often cannot find subtitles for your Anime. Note that increasing the value will decrease the performance of the search for each Episode.",
      },
    ],
    message: "Requires AniDB Integration.",
  },
  {
    key: "avistaz",
    name: "AvistaZ",
    description:
      "avistaz.to - AvistaZ is an Asian torrent tracker for HD movies, TV shows and music",
    inputs: [
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
    ],
  },
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
      "Provider removed from Bazarr because it was causing too many issues.\nIt will always return no subtitles.",
  },
  {
    key: "cinemaz",
    name: "CinemaZ",
    description:
      "cinemaz.to - CinemaZ is a private torrent tracker which is dedicated to little-known\nand cult films that you will not find on other popular torrent resources.",
    inputs: [
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
    ],
  },
  {
    key: "embeddedsubtitles",
    name: "Embedded Subtitles",
    description:
      "This provider extracts embedded subtitles from your media files. You must disable 'Treat Embedded Subtitles as Downloaded' in Settings -> Subtitles for this provider to work.",
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
        key: "unknown_as_fallback",
        name: "Use subtitles with unknown info/language as fallback language",
      },
      {
        type: "text",
        key: "fallback_lang",
        name: "Fallback language",
        defaultValue: "en",
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
  {
    key: "hdbits",
    name: "HDBits.org",
    description: "Private Tracker Subtitles Provider",
    message:
      "You must have 2FA enabled and whitelist your IP if you are running from a server.",
    inputs: [
      {
        type: "text",
        key: "username",
      },
      {
        type: "password",
        key: "passkey",
        name: "Your profile's passkey",
      },
    ],
  },
  {
    key: "jimaku",
    name: "Jimaku.cc",
    description: "Japanese Subtitles Provider",
    message:
      "API key required. Subtitles stem from various sources and might have quality/timing issues.",
    inputs: [
      {
        type: "password",
        key: "api_key",
        name: "API key",
      },
      {
        type: "switch",
        key: "enable_name_search_fallback",
        name: "Search by name if no AniList ID was determined (Less accurate, required for live action)",
      },
      {
        type: "switch",
        key: "enable_archives_download",
        name: "Also consider archives alongside uncompressed subtitles",
      },
      {
        type: "switch",
        key: "enable_ai_subs",
        name: "Download AI generated subtitles",
      },
    ],
  },
  { key: "hosszupuska", description: "Hungarian Subtitles Provider" },
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
    key: "legendasnet",
    name: "Legendas.net",
    description: "Brazilian Subtitles Provider",
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
    key: "napiprojekt",
    description: "Polish Subtitles Provider",
    inputs: [
      {
        type: "switch",
        key: "only_authors",
        name: "Skip subtitles without authors or possibly AI generated",
      },
      {
        type: "switch",
        key: "only_real_names",
        name: "Download subtitles with real name authors only",
      },
    ],
  },
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
    description: "Only works if you have VIP status",
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
        validation: {
          rule: (value: string) =>
            /^.\S+@\S+$/.test(value)
              ? "Invalid Username. Do not use your e-mail."
              : null,
        },
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
      {
        type: "switch",
        key: "include_ai_translated",
        name: "Include AI translated subtitles in search results",
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
    description: "Romanian Subtitles Provider",
  },
  {
    key: "soustitreseu",
    name: "Sous-Titres.eu",
    description: "Mostly French Subtitles Provider",
  },
  { key: "subdivx", description: "LATAM Spanish / Spanish Subtitles Provider" },
  {
    key: "subdl",
    inputs: [
      {
        type: "text",
        key: "api_key",
      },
    ],
  },
  {
    key: "subf2m",
    name: "subf2m.co",
    inputs: [
      {
        type: "switch",
        key: "verify_ssl",
        name: "Verify SSL",
        defaultValue: true,
      },
      {
        type: "text",
        key: "user_agent",
        name: "User-agent header",
      },
    ],
    message: "Make sure to use a unique and credible user agent.",
  },
  {
    key: "subssabbz",
    name: "Subs.sab.bz",
    description: "Bulgarian Subtitles Provider",
  },
  {
    key: "subs4free",
    name: "Subs4Free",
    description: "Greek Subtitles Provider. Broken, may not work for some.",
  },
  {
    key: "subs4series",
    name: "Subs4Series",
    description:
      "Greek Subtitles Provider.\nRequires anti-captcha provider to solve captchas for each download.",
  },
  { key: "subscenter", description: "Hebrew Subtitles Provider" },
  {
    key: "subsro",
    name: "subs.ro",
    description: "Romanian Subtitles Provider",
  },
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
    key: "titulky",
    name: "Titulky.com",
    description: "CZ/SK Subtitles Provider. Available only with VIP.",
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
      {
        type: "switch",
        key: "skip_wrong_fps",
        name: "Skip subtitles with mismatched fps to video's",
      },
    ],
  },
  {
    key: "turkcealtyaziorg",
    name: "Turkcealtyazi.org",
    description: "Turkish Subtitles Provider",
    message:
      "For requests coming from outside of Turkey, cookies and user agent are required. Especially cf_clearance cookie.",
    inputs: [
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
    ],
  },
  { key: "tvsubtitles", name: "TVSubtitles" },
  {
    key: "whisperai",
    name: "Whisper",
    description: "AI Generated Subtitles powered by Whisper",
    inputs: [
      {
        type: "text",
        key: "endpoint",
        defaultValue: "http://127.0.0.1:9000",
        name: "Whisper ASR Docker Endpoint",
      },
      {
        type: "text",
        key: "response",
        defaultValue: 5,
        name: "Connection/response timeout in seconds",
      },
      {
        type: "text",
        key: "timeout",
        defaultValue: 3600,
        name: "Transcription/translation timeout in seconds",
      },
      {
        type: "select",
        key: "loglevel",
        name: "Logging level",
        options: logLevelOptions,
      },
      {
        type: "switch",
        key: "pass_video_name",
        name: "Pass video filename to Whisper (for logging)",
        defaultValue: false,
      },
      {
        type: "testbutton",
        key: "whisperai",
        name: "Test Connection button",
      },
    ],
  },
  { key: "wizdom", description: "Wizdom.xyz Subtitles Provider" },
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
  {
    key: "zimuku",
    name: "Zimuku",
    description: "Chinese Subtitles Provider. Anti-captcha required.",
  },
];

export const IntegrationList: Readonly<ProviderInfo[]> = [
  {
    key: "anidb",
    name: "AniDB",
    description:
      "AniDB is non-profit database of anime information that is freely open to the public.",
    inputs: [
      {
        type: "text",
        key: "api_client",
        name: "API Client",
      },
      {
        type: "text",
        key: "api_client_ver",
        name: "API Client Version",
      },
    ],
  },
];
