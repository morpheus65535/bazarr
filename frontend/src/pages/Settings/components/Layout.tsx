import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { Toolbox } from "@/components";
import { LoadingProvider } from "@/contexts";
import { useOnValueChange } from "@/utilities";
import { faSave } from "@fortawesome/free-solid-svg-icons";
import { Container, Group, LoadingOverlay } from "@mantine/core";
import { useDocumentTitle, useForm } from "@mantine/hooks";
import { FunctionComponent, ReactNode, useCallback } from "react";
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
    },
    validationRules: {
      settings: (value) => Object.keys(value).length > 0,
    },
  });

  useOnValueChange(isRefetching, (value) => {
    if (!value) {
      form.reset();
    }
  });

  const submit = useCallback((values: FormValues) => {
    //
  }, []);

  // const updateStorage = useUpdateLocalStorage();

  // const [dispatcher, setDispatcher] = useState<SettingDispatcher>({});

  // useEffect(() => {
  //   if (isRefetching === false) {
  //     // form.reset();
  //   }
  // }, [isRefetching]);

  // const saveSettings = useCallback(
  //   (settings: LooseObject) => {
  //     submitHooks(settings);
  //     LOG("info", "submitting settings", settings);
  //     mutate(settings);
  //   },
  //   [mutate]
  // );

  // const saveLocalStorage = useCallback(
  //   (settings: LooseObject) => {
  //     updateStorage(settings);
  //     form.reset();
  //   },
  //   [form, updateStorage]
  // );

  // useEffect(() => {
  //   // Update dispatch
  //   const newDispatch: SettingDispatcher = {};
  //   newDispatch["__default__"] = saveSettings;
  //   newDispatch["storage"] = saveLocalStorage;
  //   setDispatcher(newDispatch);
  // }, [saveSettings, saveLocalStorage]);

  // const defaultDispatcher = useMemo(
  //   () => dispatcher["__default__"],
  //   [dispatcher]
  // );

  // const submit = useCallback(() => {
  //   const dispatchMaps = new Map<string, LooseObject>();
  //   const stagedChange = form.values.settings;

  //   // Separate settings by key
  //   for (const key in stagedChange) {
  //     const keys = key.split("-");
  //     const firstKey = keys[0];
  //     if (firstKey.length === 0) {
  //       continue;
  //     }

  //     const object = dispatchMaps.get(firstKey);
  //     if (object) {
  //       object[key] = stagedChange[key];
  //     } else {
  //       dispatchMaps.set(firstKey, { [key]: stagedChange[key] });
  //     }
  //   }

  //   let lostValues = {};

  //   dispatchMaps.forEach((v, k) => {
  //     if (k in dispatcher) {
  //       dispatcher[k](v);
  //     } else {
  //       lostValues = merge(lostValues, v);
  //     }
  //   });
  //   // send to default dispatcher
  //   defaultDispatcher(lostValues);
  // }, [form.values.settings, defaultDispatcher, dispatcher]);

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
                disabled={Object.keys(form.values.settings).length === 0}
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
