import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { LoadingProvider } from "@/contexts";
import { useOnValueChange } from "@/utilities";
import { LOG } from "@/utilities/console";
import { usePrompt } from "@/utilities/routers";
import { useUpdateLocalStorage } from "@/utilities/storage";
import { faSave } from "@fortawesome/free-solid-svg-icons";
import { Badge, Container, Group, LoadingOverlay } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useDocumentTitle } from "@mantine/hooks";
import { FunctionComponent, ReactNode, useCallback, useMemo } from "react";
import { FormContext, FormValues } from "../utilities/FormValues";
import {
  SubmitHooksProvider,
  useSubmitHooksSource,
} from "../utilities/HooksProvider";
import { SettingsProvider } from "../utilities/SettingsProvider";

interface Props {
  name: string;
  children: ReactNode;
}

const Layout: FunctionComponent<Props> = (props) => {
  const { children, name } = props;

  const { data: settings, isLoading, isRefetching } = useSystemSettings();
  const { mutate, isLoading: isMutating } = useSettingsMutation();

  const submitHooks = useSubmitHooksSource();

  const form = useForm<FormValues>({
    initialValues: {
      settings: {},
      storages: {},
    },
  });

  useOnValueChange(isRefetching, (value) => {
    if (!value) {
      form.setValues((values) => ({ ...values, settings: {} }));
    }
  });

  const updateStorage = useUpdateLocalStorage();

  const submit = useCallback(
    (values: FormValues) => {
      const { settings, storages } = values;

      if (Object.keys(settings).length > 0) {
        const settingsToSubmit = { ...settings };
        submitHooks.invoke(settingsToSubmit);
        LOG("info", "submitting settings", settingsToSubmit);
        mutate(settingsToSubmit);
      }

      if (Object.keys(storages).length > 0) {
        const storagesToSubmit = { ...storages };
        LOG("info", "submitting storages", storagesToSubmit);
        updateStorage(storagesToSubmit);

        form.setValues((values) => ({ ...values, storages: {} }));
      }
    },
    [form, mutate, submitHooks, updateStorage]
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
        <SubmitHooksProvider value={submitHooks}>
          <form onSubmit={form.onSubmit(submit)}>
            <Toolbox>
              <Group>
                <Toolbox.Button
                  type="submit"
                  icon={faSave}
                  loading={isMutating}
                  disabled={totalStagedCount === 0}
                  rightIcon={
                    <Badge
                      size="xs"
                      radius="sm"
                      hidden={totalStagedCount === 0}
                    >
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
        </SubmitHooksProvider>
      </LoadingProvider>
    </SettingsProvider>
  );
};

export default Layout;
