import { FunctionComponent, useMemo } from "react";
import { useLanguages } from "@/apis/hooks";
import { Selector, SelectorProps } from "@/components/inputs";
import { useSelectorOptions } from "@/utilities";

interface LanguageSelectorProps
  extends Omit<SelectorProps<Language.Server>, "options" | "getkey"> {
  enabled?: boolean;
}

const LanguageSelector: FunctionComponent<LanguageSelectorProps> = ({
  enabled = false,
  ...selector
}) => {
  const { data } = useLanguages();

  const filteredData = useMemo(() => {
    if (enabled) {
      return data?.filter((value) => value.enabled);
    } else {
      return data;
    }
  }, [data, enabled]);

  const options = useSelectorOptions(
    filteredData ?? [],
    (value) => value.name,
    (value) => value.code3,
  );

  return <Selector {...options} searchable {...selector}></Selector>;
};

export default LanguageSelector;
