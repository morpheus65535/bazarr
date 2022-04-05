import { useSettingsMutation, useSystemSettings } from "@/apis/hooks";
import { ContentHeader, LoadingIndicator } from "@/components";
import { LOG } from "@/utilities/console";
import { useUpdateLocalStorage } from "@/utilities/storage";
import { faSave } from "@fortawesome/free-solid-svg-icons";
import { Container, Stack } from "@mantine/core";
import { merge } from "lodash";
import {
  createContext,
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Helmet } from "react-helmet";
import {
  enabledLanguageKey,
  languageProfileKey,
  notificationsKey,
} from "../keys";

type SettingDispatcher = Record<string, (settings: LooseObject) => void>;

export const StagedChangesContext = createContext<SimpleStateType<LooseObject>>(
  [
    {},
    () => {
      throw new Error("StagedChangesContext not initialized");
    },
  ]
);

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
  children: JSX.Element | JSX.Element[];
}

const Layout: FunctionComponent<Props> = (props) => {
  const { children, name } = props;

  const updateStorage = useUpdateLocalStorage();

  const [stagedChange, setChange] = useState<LooseObject>({});
  const [dispatcher, setDispatcher] = useState<SettingDispatcher>({});

  const { isLoading, isRefetching } = useSystemSettings();
  const { mutate, isLoading: isMutating } = useSettingsMutation();

  useEffect(() => {
    if (isRefetching === false) {
      setChange({});
    }
  }, [isRefetching]);

  const saveSettings = useCallback(
    (settings: LooseObject) => {
      submitHooks(settings);
      LOG("info", "submitting settings", settings);
      mutate(settings);
    },
    [mutate]
  );

  const saveLocalStorage = useCallback(
    (settings: LooseObject) => {
      updateStorage(settings);
      setChange({});
    },
    [updateStorage]
  );

  useEffect(() => {
    // Update dispatch
    const newDispatch: SettingDispatcher = {};
    newDispatch["__default__"] = saveSettings;
    newDispatch["storage"] = saveLocalStorage;
    setDispatcher(newDispatch);
  }, [saveSettings, saveLocalStorage]);

  const defaultDispatcher = useMemo(
    () => dispatcher["__default__"],
    [dispatcher]
  );

  const submit = useCallback(() => {
    const dispatchMaps = new Map<string, LooseObject>();

    // Separate settings by key
    for (const key in stagedChange) {
      const keys = key.split("-");
      const firstKey = keys[0];
      if (firstKey.length === 0) {
        continue;
      }

      const object = dispatchMaps.get(firstKey);
      if (object) {
        object[key] = stagedChange[key];
      } else {
        dispatchMaps.set(firstKey, { [key]: stagedChange[key] });
      }
    }

    let lostValues = {};

    dispatchMaps.forEach((v, k) => {
      if (k in dispatcher) {
        dispatcher[k](v);
      } else {
        lostValues = merge(lostValues, v);
      }
    });
    // send to default dispatcher
    defaultDispatcher(lostValues);
  }, [stagedChange, dispatcher, defaultDispatcher]);

  if (isLoading) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <Container fluid px={0}>
      <Helmet>
        <title>{name} - Bazarr (Settings)</title>
      </Helmet>
      {/* TODO */}
      {/* <Prompt
        when={Object.keys(stagedChange).length > 0}
        message="You have unsaved changes, are you sure you want to leave?"
      ></Prompt> */}
      <Stack>
        <ContentHeader>
          <ContentHeader.Button
            icon={faSave}
            updating={isMutating}
            disabled={Object.keys(stagedChange).length === 0}
            onClick={submit}
          >
            Save
          </ContentHeader.Button>
        </ContentHeader>
        <StagedChangesContext.Provider value={[stagedChange, setChange]}>
          {children}
        </StagedChangesContext.Provider>
      </Stack>
    </Container>
  );
};

export default Layout;
