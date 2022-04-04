import { LanguageSelector } from "@/components/LanguageSelector";
import { useModal, withModal } from "@/modules/modals";
import { useEnabledLanguages } from "@/utilities/languages";
import { Button, Text } from "@mantine/core";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { useProcess } from "./ToolContext";
import { availableTranslation } from "./tools";

const TranslationTool: FunctionComponent = () => {
  const { data: languages } = useEnabledLanguages();

  const available = useMemo(
    () => languages.filter((v) => v.code2 in availableTranslation),
    [languages]
  );

  const Modal = useModal();

  const [selectedLanguage, setLanguage] =
    useState<Nullable<Language.Info>>(null);

  const process = useProcess();

  const submit = useCallback(() => {
    if (selectedLanguage) {
      process("translate", { language: selectedLanguage.code2 });
    }
  }, [process, selectedLanguage]);

  const footer = (
    <Button disabled={!selectedLanguage} onClick={submit}>
      Translate
    </Button>
  );
  return (
    <Modal title="Translation" footer={footer}>
      <Text>
        Enabled languages not listed here are unsupported by Google Translate.
      </Text>
      <LanguageSelector
        options={available}
        onChange={setLanguage}
      ></LanguageSelector>
    </Modal>
  );
};

export default withModal(TranslationTool, "translation-tool");
