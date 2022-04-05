import { Selector } from "@/components";
import { Language } from "@/components/bazarr";
import { useModal, withModal } from "@/modules/modals";
import { useSelectorOptions } from "@/utilities";
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

  const options = useSelectorOptions(available, (v) => v.name);

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
      <Selector {...options} onChange={setLanguage}></Selector>
    </Modal>
  );
};

export default withModal(TranslationTool, "translation-tool");
