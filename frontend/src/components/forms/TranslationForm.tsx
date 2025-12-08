import { FunctionComponent, useMemo } from "react";
import { Alert, Button, Divider, Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { isObject } from "lodash";
import { useSubtitleAction } from "@/apis/hooks";
import { useSystemSettings } from "@/apis/hooks";
import { Selector } from "@/components/inputs";
import { useModals, withModal } from "@/modules/modals";
import { useSelectorOptions } from "@/utilities";
import FormUtils from "@/utilities/form";
import { useEnabledLanguages } from "@/utilities/languages";

const translations = {
  af: "afrikaans",
  sq: "albanian",
  am: "amharic",
  ar: "arabic",
  hy: "armenian",
  az: "azerbaijani",
  eu: "basque",
  be: "belarusian",
  bn: "bengali",
  bs: "bosnian",
  bg: "bulgarian",
  ca: "catalan",
  ceb: "cebuano",
  ny: "chichewa",
  zh: "chinese (simplified)",
  zt: "chinese (traditional)",
  co: "corsican",
  hr: "croatian",
  cs: "czech",
  da: "danish",
  nl: "dutch",
  en: "english",
  eo: "esperanto",
  et: "estonian",
  tl: "filipino",
  fi: "finnish",
  fr: "french",
  fy: "frisian",
  gl: "galician",
  ka: "georgian",
  de: "german",
  el: "greek",
  gu: "gujarati",
  ht: "haitian creole",
  ha: "hausa",
  haw: "hawaiian",
  iw: "hebrew",
  hi: "hindi",
  hmn: "hmong",
  hu: "hungarian",
  is: "icelandic",
  ig: "igbo",
  id: "indonesian",
  ga: "irish",
  it: "italian",
  ja: "japanese",
  jw: "javanese",
  kn: "kannada",
  kk: "kazakh",
  km: "khmer",
  ko: "korean",
  ku: "kurdish (kurmanji)",
  ky: "kyrgyz",
  lo: "lao",
  la: "latin",
  lv: "latvian",
  lt: "lithuanian",
  lb: "luxembourgish",
  mk: "macedonian",
  mg: "malagasy",
  ms: "malay",
  ml: "malayalam",
  mt: "maltese",
  mi: "maori",
  mr: "marathi",
  mn: "mongolian",
  my: "myanmar (burmese)",
  ne: "nepali",
  no: "norwegian",
  ps: "pashto",
  fa: "persian",
  pl: "polish",
  pt: "portuguese",
  pa: "punjabi",
  ro: "romanian",
  ru: "russian",
  sm: "samoan",
  gd: "scots gaelic",
  sr: "serbian",
  st: "sesotho",
  sn: "shona",
  sd: "sindhi",
  si: "sinhala",
  sk: "slovak",
  sl: "slovenian",
  so: "somali",
  es: "spanish",
  su: "sundanese",
  sw: "swahili",
  sv: "swedish",
  tg: "tajik",
  ta: "tamil",
  te: "telugu",
  th: "thai",
  tr: "turkish",
  uk: "ukrainian",
  ur: "urdu",
  uz: "uzbek",
  vi: "vietnamese",
  cy: "welsh",
  xh: "xhosa",
  yi: "yiddish",
  yo: "yoruba",
  zu: "zulu",
  fil: "Filipino",
  he: "Hebrew",
};

interface Props {
  selections: FormType.ModifySubtitle[];
  onSubmit?: VoidFunction;
}

interface TranslationConfig {
  service: string;
  model: string;
}

const TranslationForm: FunctionComponent<Props> = ({
  selections,
  onSubmit,
}) => {
  const settings = useSystemSettings();
  const { mutateAsync } = useSubtitleAction();
  const modals = useModals();

  const { data: languages } = useEnabledLanguages();

  const form = useForm({
    initialValues: {
      language: null as Language.Info | null,
    },
    validate: {
      language: FormUtils.validation(isObject, "Please select a language"),
    },
  });

  const translatorType = settings?.data?.translator?.translator_type;
  const isGoogleTranslator = translatorType === "google_translate";

  const available = useMemo(() => {
    // Only filter by translations if using Google Translate
    if (isGoogleTranslator) {
      return languages.filter((v) => v.code2 in translations);
    }
    // For other translators, return all enabled languages
    return languages;
  }, [languages, isGoogleTranslator]);

  const options = useSelectorOptions(
    available,
    (v) => v.name,
    (v) => v.code2,
  );

  const getTranslationConfig = (
    settings: ReturnType<typeof useSystemSettings>,
  ): TranslationConfig => {
    const translatorType = settings?.data?.translator?.translator_type;
    const defaultConfig: TranslationConfig = {
      service: "Google Translate",
      model: "",
    };

    switch (translatorType) {
      case "gemini":
        return {
          ...defaultConfig,
          service: "Gemini",
          model: ` (${settings?.data?.translator?.gemini_model || ""})`,
        };
      case "lingarr":
        return {
          ...defaultConfig,
          service: "Lingarr",
        };
      default:
        return defaultConfig;
    }
  };

  // In the component, replace lines 167-185 with:
  const config = getTranslationConfig(settings);
  const translatorService = config.service;
  const translatorModel = config.model;

  return (
    <form
      onSubmit={form.onSubmit(({ language }) => {
        if (language) {
          selections.forEach(
            async (s) =>
              await mutateAsync({
                action: "translate",
                form: {
                  ...s,
                  language: language.code2,
                },
              }),
          );

          onSubmit?.();
          modals.closeSelf();
        }
      })}
    >
      <Stack>
        <Alert>
          <div>
            {translatorService}
            {translatorModel} will be used.
          </div>
          <div>
            You can choose translation service in the subtitles settings.
          </div>
        </Alert>
        {isGoogleTranslator && (
          <Alert variant="outline">
            Enabled languages not listed here are unsupported by{" "}
            {translatorService}.
          </Alert>
        )}
        <Selector {...options} {...form.getInputProps("language")}></Selector>
        <Divider></Divider>
        <Button type="submit">Start</Button>
      </Stack>
    </form>
  );
};

export const TranslationModal = withModal(TranslationForm, "translation-tool", {
  title: "Translate Subtitle(s)",
});

export default TranslationForm;
