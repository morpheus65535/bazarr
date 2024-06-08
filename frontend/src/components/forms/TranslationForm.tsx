import { FunctionComponent, useMemo } from "react";
import { Alert, Button, Divider, Stack } from "@mantine/core";
import { useForm } from "@mantine/form";
import { isObject } from "lodash";
import { useSubtitleAction } from "@/apis/hooks";
import { Selector } from "@/components/inputs";
import { useModals, withModal } from "@/modules/modals";
import { task } from "@/modules/task";
import { useSelectorOptions } from "@/utilities";
import FormUtils from "@/utilities/form";
import { useEnabledLanguages } from "@/utilities/languages";

const TaskName = "Translating Subtitles";

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

const TranslationForm: FunctionComponent<Props> = ({
  selections,
  onSubmit,
}) => {
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

  const available = useMemo(
    () => languages.filter((v) => v.code2 in translations),
    [languages],
  );

  const options = useSelectorOptions(
    available,
    (v) => v.name,
    (v) => v.code2,
  );

  return (
    <form
      onSubmit={form.onSubmit(({ language }) => {
        if (language) {
          selections.forEach((s) =>
            task.create(s.path, TaskName, mutateAsync, {
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
        <Alert variant="outline">
          Enabled languages not listed here are unsupported by Google Translate.
        </Alert>
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
