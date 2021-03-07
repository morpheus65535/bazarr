import { faSave } from "@fortawesome/free-solid-svg-icons";
import { merge } from "lodash";
import React, {
  FunctionComponent,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Prompt } from "react-router";
import {
  siteSaveLocalstorage,
  systemUpdateSettingsAll,
} from "../../@redux/actions";
import { useSystemSettings } from "../../@redux/hooks";
import { useReduxAction, useReduxActionWith } from "../../@redux/hooks/base";
import { SystemApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import {
  enabledLanguageKey,
  languageProfileKey,
  notificationsKey,
} from "../keys";

type SettingDispatcher = Record<string, (settings: LooseObject) => void>;

export type UpdateFunctionType = (v: any, k?: string) => void;

export const UpdateChangeContext = React.createContext<UpdateFunctionType>(
  (v: any, k?: string) => {}
);

const SettingsContext = React.createContext<Nullable<Settings>>(null);

export const StagedChangesContext = React.createContext<LooseObject>({});

export function useLocalSettings(): Settings {
  const settings = useContext(SettingsContext);
  if (process.env.NODE_ENV === "development") {
    console.assert(
      settings !== null,
      "useSettings hook was invoked outside of SettingsProvider!"
    );
  }
  return settings!;
}

export function useLocalUpdater(): UpdateFunctionType {
  return useContext(UpdateChangeContext);
}

export function useStagedValues(): LooseObject {
  return useContext(StagedChangesContext);
}

function submitHooks(settings: LooseObject) {
  if (languageProfileKey in settings) {
    const item = settings[languageProfileKey];
    settings[languageProfileKey] = JSON.stringify(item);
  }

  if (enabledLanguageKey in settings) {
    const item = settings[enabledLanguageKey] as Language[];
    settings[enabledLanguageKey] = item.map((v) => v.code2);
  }

  if (notificationsKey in settings) {
    const item = settings[notificationsKey] as Settings.NotificationInfo[];
    settings[notificationsKey] = item.map((v) => JSON.stringify(v));
  }
}

interface Props {
  title: string;
  children: JSX.Element | JSX.Element[];
}

const SettingsProvider: FunctionComponent<Props> = (props) => {
  const { children, title } = props;

  const [settings] = useSystemSettings();
  const updateStorage = useReduxAction(siteSaveLocalstorage);

  const [stagedChange, setChange] = useState<LooseObject>({});
  const [updating, setUpdating] = useState(false);
  const [dispatcher, setDispatcher] = useState<SettingDispatcher>({});

  const cleanup = useCallback(() => {
    setChange({});
    setUpdating(false);
  }, []);

  const update = useReduxActionWith(systemUpdateSettingsAll, cleanup);

  const updateChange = useCallback<UpdateFunctionType>(
    (v: any, k?: string) => {
      if (k) {
        const newChanges = { ...stagedChange };
        newChanges[k] = v;

        if (process.env.NODE_ENV === "development") {
          console.log("staged settings", newChanges);
        }

        setChange(newChanges);
      }
    },
    [stagedChange]
  );

  const saveSettings = useCallback(
    (settings: LooseObject) => {
      submitHooks(settings);
      setUpdating(true);
      console.log("submitting settings", settings);
      SystemApi.setSettings(settings).finally(update);
    },
    [update]
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

  const defaultDispatcher = useMemo(() => dispatcher["__default__"], [
    dispatcher,
  ]);

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

  return (
    <AsyncStateOverlay state={settings}>
      {(data) => (
        <Container fluid>
          <Helmet>
            <title>{title}</title>
          </Helmet>
          <Prompt
            when={Object.keys(stagedChange).length > 0}
            message="You have unsaved changes, are you sure you want to leave?"
          ></Prompt>
          <ContentHeader>
            <ContentHeader.Button
              icon={faSave}
              updating={updating}
              disabled={Object.keys(stagedChange).length === 0}
              onClick={submit}
            >
              Save
            </ContentHeader.Button>
          </ContentHeader>
          <SettingsContext.Provider value={data}>
            <UpdateChangeContext.Provider value={updateChange}>
              <StagedChangesContext.Provider value={stagedChange}>
                <Row className="p-4">
                  <Container>{children}</Container>
                </Row>
              </StagedChangesContext.Provider>
            </UpdateChangeContext.Provider>
          </SettingsContext.Provider>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default SettingsProvider;
