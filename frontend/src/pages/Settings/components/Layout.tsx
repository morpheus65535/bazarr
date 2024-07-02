import { FunctionComponent, ReactNode, useCallback, useMemo } from "react";
import { Badge, Container, Group, LoadingOverlay } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useDocumentTitle } from "@mantine/hooks";
import { faSave } from "@fortawesome/free-solid-svg-icons";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { LoadingProvider } from "@/contexts";
import {
  FormContext,
  FormValues,
  runHooks,
} from "@/pages/Settings/utilities/FormValues";
import { SettingsProvider } from "@/pages/Settings/utilities/SettingsProvider";
import { useOnValueChange } from "@/utilities";
import { LOG } from "@/utilities/console";
import { usePrompt } from "@/utilities/routers";

interface Props {
  name: string;
  children: ReactNode;
}

const Layout: FunctionComponent<Props> = (props) => {
  const { children, name } = props;

  const { data: settings, isLoading, isRefetching } = useSystemSettings();
  const { mutate, isPending: isMutating } = useSettingsMutation();

  const form = useForm<FormValues>({
    initialValues: {
      settings: {},
      hooks: {},
    },
  });

  useOnValueChange(isRefetching, (value) => {
    if (!value) {
      form.reset();
    }
  });

  const submit = useCallback(
    (values: FormValues) => {
      const { settings, hooks } = values;

      if (Object.keys(settings).length > 0) {
        const settingsToSubmit = { ...settings };
        runHooks(hooks, settingsToSubmit);
        LOG("info", "submitting settings", settingsToSubmit);
        mutate(settingsToSubmit);
      }
    },
    [mutate],
  );

  const totalStagedCount = useMemo(() => {
    return Object.keys(form.values.settings).length;
  }, [form.values.settings]);

  usePrompt(
    totalStagedCount > 0,
    `You have ${totalStagedCount} unsaved changes, are you sure you want to leave?`,
  );

  useDocumentTitle(`${name} - Bazarr (Settings)`);

  return (
    <SettingsProvider value={settings ?? null}>
      <LoadingProvider value={isLoading || isMutating}>
        <form onSubmit={form.onSubmit(submit)} style={{ position: "relative" }}>
          <LoadingOverlay visible={settings === undefined}></LoadingOverlay>
          <Toolbox>
            <Group>
              <Toolbox.Button
                type="submit"
                icon={faSave}
                loading={isMutating}
                disabled={totalStagedCount === 0}
                rightSection={
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
