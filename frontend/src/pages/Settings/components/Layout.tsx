import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { LoadingProvider } from "@/contexts";
import { useOnValueChange } from "@/utilities";
import { LOG } from "@/utilities/console";
import { useUpdateLocalStorage } from "@/utilities/storage";
import { faSave } from "@fortawesome/free-solid-svg-icons";
import { Container, Group, LoadingOverlay } from "@mantine/core";
import { useDocumentTitle, useForm } from "@mantine/hooks";
import { FunctionComponent, ReactNode, useCallback, useMemo } from "react";
import {
  enabledLanguageKey,
  languageProfileKey,
  notificationsKey,
} from "../keys";
import { FormContext, FormValues } from "../utilities/FormValues";
import { SettingsProvider } from "../utilities/SettingsProvider";

function submitHooks(settings: LooseObject) {
  if (languageProfileKey in settings) {
    const item = settings[languageProfileKey];
    settings[languageProfileKey] = JSON.stringify(item);
  }

  if (enabledLanguageKey in settings) {
    const item = settings[enabledLanguageKey] as Language.Info[];
    settings[enabledLanguageKey] = item.map((v) => v.code2);
  }

  if (notificationsKey in settings) {
    const item = settings[notificationsKey] as Settings.NotificationInfo[];
    settings[notificationsKey] = item.map((v) => JSON.stringify(v));
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
        submitHooks(settings);
        LOG("info", "submitting settings", settings);
        mutate(settings);
      }

      if (Object.keys(storages).length > 0) {
        LOG("info", "submitting storages", storages);
        updateStorage(storages);
      }
    },
    [mutate, updateStorage]
  );

  const totalStagedCount = useMemo(() => {
    const object = { ...form.values.settings, ...form.values.storages };

    return Object.keys(object).length;
  }, [form.values.settings, form.values.storages]);

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
