import { FunctionComponent, ReactNode, useMemo } from "react";
import { Badge, Container, Group, LoadingOverlay } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useDocumentTitle } from "@mantine/hooks";
import { faRotateLeft, faSave } from "@fortawesome/free-solid-svg-icons";
import { isEqual } from "lodash";
import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { useInstanceName } from "@/apis/hooks/site";
import { Toolbox } from "@/components";
import { LoadingProvider } from "@/contexts";
import {
  FormContext,
  FormValues,
  runHooks,
} from "@/pages/Settings/utilities/FormValues";
import { SettingsProvider } from "@/pages/Settings/utilities/SettingsProvider";
import { LOG } from "@/utilities/console";
import { usePrompt } from "@/utilities/routers";

interface Props {
  name: string;
  children: ReactNode;
  /** True while an in-page editor owns the content (e.g. a profile editor). */
  isEditorActive?: boolean;
  /** True when that editor holds changes that have not been applied yet. */
  isDraftDirty?: boolean;
}

const Layout: FunctionComponent<Props> = (props) => {
  const {
    children,
    name,
    isEditorActive = false,
    isDraftDirty = false,
  } = props;

  const { data: settings, isLoading } = useSystemSettings();
  const { mutate, isPending: isMutating } = useSettingsMutation();

  const form = useForm<FormValues>({
    initialValues: {
      settings: {},
      hooks: {},
    },
  });

  const submit = (values: FormValues) => {
    // An in-page editor must be applied or cancelled before settings are saved.
    if (isEditorActive) {
      return;
    }

    const { settings, hooks } = values;

    if (Object.keys(settings).length > 0) {
      const submittedSettings = { ...settings };
      const settingsToSubmit = { ...settings };
      runHooks(hooks, settingsToSubmit);
      LOG("info", "submitting settings", settingsToSubmit);
      mutate(settingsToSubmit, {
        onSuccess: () => {
          // Clear only successfully saved values that have not changed again
          // since submission. External refetches never discard local edits.
          form.setValues((current) => {
            const nextSettings = { ...current.settings };
            const nextHooks = { ...current.hooks };

            for (const [key, submittedValue] of Object.entries(
              submittedSettings,
            )) {
              if (isEqual(current.settings?.[key], submittedValue)) {
                delete nextSettings[key];
                delete nextHooks[key];
              }
            }

            return {
              ...current,
              settings: nextSettings,
              hooks: nextHooks,
            };
          });
        },
      });
    }
  };

  const totalStagedCount = useMemo(() => {
    return Object.keys(form.values.settings).length;
  }, [form.values.settings]);

  const isLeaveBlocked =
    totalStagedCount > 0 || (isEditorActive && isDraftDirty);

  usePrompt(
    isLeaveBlocked,
    totalStagedCount > 0
      ? `You have ${totalStagedCount} unsaved changes, are you sure you want to leave?`
      : "You have an unsaved profile edit, are you sure you want to leave?",
  );

  useDocumentTitle(`${name} - ${useInstanceName()} (Settings)`);

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
                data-onboarding="settings-save"
                loading={isMutating}
                disabled={isEditorActive || totalStagedCount === 0}
                rightSection={
                  <Badge size="xs" radius="sm" hidden={totalStagedCount === 0}>
                    {totalStagedCount}
                  </Badge>
                }
              >
                Save
              </Toolbox.Button>
              <Toolbox.Button
                type="button"
                icon={faRotateLeft}
                disabled={
                  isEditorActive || totalStagedCount === 0 || isMutating
                }
                onClick={() => {
                  form.reset();
                }}
              >
                Discard
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
