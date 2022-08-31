import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { LoadingProvider } from "@/contexts";
import { useOnValueChange } from "@/utilities";
import { LOG } from "@/utilities/console";
import { usePrompt } from "@/utilities/routers";
import { useUpdateLocalStorage } from "@/utilities/storage";
import { faSave } from "@fortawesome/free-solid-svg-icons";
import { Badge, Container, Group, LoadingOverlay } from "@mantine/core";
import { useDocumentTitle, useForm } from "@mantine/hooks";
import { FunctionComponent, ReactNode, useCallback, useMemo } from "react";
import { enabledLanguageKey, languageProfileKey } from "../keys";
import { FormContext, FormValues } from "../utilities/FormValues";
import { SettingsProvider } from "../utilities/SettingsProvider";

type SubmitHookType = {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: (value: any) => unknown;
};

export const submitHooks: SubmitHookType = {
  [languageProfileKey]: (value) => JSON.stringify(value),
  [enabledLanguageKey]: (value: Language.Info[]) => value.map((v) => v.code2),
};

function invokeHooks(settings: LooseObject) {
  for (const key in settings) {
    if (key in submitHooks) {
      const value = settings[key];
      const fn = submitHooks[key];
      settings[key] = fn(value);
    }
  }
}

interface Props {
  name: string;
  children: ReactNode;
}

const Layout: FunctionComponent<Props> = (props) => {
  const { children, name } = props;

  const { data: settings, isLoading, isRefetching } = useSystemSettings();
  const { mutate, isLoading: isMutating } = useSettingsMutation();

  const form = useForm<FormValues>({
    initialValues: {
      settings: {},
      storages: {},
    },
  });

  useOnValueChange(isRefetching, (value) => {
    if (!value) {
      form.reset();
    }
  });

  const updateStorage = useUpdateLocalStorage();

  const submit = useCallback(
    (values: FormValues) => {
      const { settings, storages } = values;

      if (Object.keys(settings).length > 0) {
        const settingsToSubmit = { ...settings };
        invokeHooks(settingsToSubmit);
        LOG("info", "submitting settings", settingsToSubmit);
        mutate(settingsToSubmit);
      }

      if (Object.keys(storages).length > 0) {
        const storagesToSubmit = { ...storages };
        LOG("info", "submitting storages", storagesToSubmit);
        updateStorage(storagesToSubmit);
      }
    },
    [mutate, updateStorage]
  );

  const totalStagedCount = useMemo(() => {
    const object = { ...form.values.settings, ...form.values.storages };

    return Object.keys(object).length;
  }, [form.values.settings, form.values.storages]);

  usePrompt(
    totalStagedCount > 0,
    `You have ${totalStagedCount} unsaved changes, are you sure you want to leave?`
  );

  useDocumentTitle(`${name} - Bazarr (Settings)`);

  if (settings === undefined) {
    return <LoadingOverlay visible></LoadingOverlay>;
  }

  return (
    <SettingsProvider value={settings}>
      <LoadingProvider value={isLoading || isMutating}>
        <form onSubmit={form.onSubmit(submit)}>
          <Toolbox>
            <Group>
              <Toolbox.Button
                type="submit"
                icon={faSave}
                loading={isMutating}
                disabled={totalStagedCount === 0}
                rightIcon={
                  <Badge size="xs" radius="sm" hidden={totalStagedCount === 0}>
                    {totalStagedCount}
                  </Badge>
                }
              >
                Save
              </Toolbox.Button>
            </Group>
          </Toolbox>
          <FormContext.Provider value={form}>
            <Container size="xl" mx={0}>
              {children}
            </Container>
          </FormContext.Provider>
        </form>
      </LoadingProvider>
    </SettingsProvider>
  );
};

export default Layout;
