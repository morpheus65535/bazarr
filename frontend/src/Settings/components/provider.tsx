import { faSave } from "@fortawesome/free-solid-svg-icons";
import React, {
  FunctionComponent,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Prompt } from "react-router";
import { siteSaveLocalstorage } from "../../@redux/actions";
import { useSystemSettings } from "../../@redux/hooks";
import { useReduxAction } from "../../@redux/hooks/base";
import { SystemApi } from "../../apis";
import { AsyncStateOverlay, ContentHeader } from "../../components";
import {
  enabledLanguageKey,
  languageProfileKey,
  notificationsKey,
} from "../keys";

export type UpdateFunctionType = (v: any, k?: string) => void;

export const UpdateChangeContext = React.createContext<UpdateFunctionType>(
  (v: any, k?: string) => {}
);

const SettingsContext = React.createContext<Settings | undefined>(undefined);

export const StagedChangesContext = React.createContext<LooseObject>({});

export function useSettings(): Settings {
  const settings = useContext(SettingsContext);
  if (process.env.NODE_ENV === "development") {
    console.assert(
      settings !== undefined,
      "useSettings hook was invoked outside of SettingsProvider!"
    );
  }
  return settings!;
}

export function useUpdate(): UpdateFunctionType {
  return useContext(UpdateChangeContext);
}

export function useStaged(): LooseObject {
  return useContext(StagedChangesContext);
}

function beforeSubmit(settings: LooseObject) {
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

type SettingDispatch = Record<string, (settings: LooseObject) => void>;

interface Props {
  title: string;
  children: JSX.Element | JSX.Element[];
}

const SettingsProvider: FunctionComponent<Props> = (props) => {
  const { children, title } = props;

  const [settings, update] = useSystemSettings();
  const updateStorage = useReduxAction(siteSaveLocalstorage);

  const [stagedChange, setChange] = useState<LooseObject>({});
  const [updating, setUpdating] = useState(false);
  const [dispatch, setDispatch] = useState<SettingDispatch>({});

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
      beforeSubmit(settings);
      setUpdating(true);
      console.log("submitting settings", settings);
      SystemApi.setSettings(settings).finally(() => {
        update();
        setChange({});
        setUpdating(false);
      });
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
    const newDispatch: SettingDispatch = {};
    newDispatch["languages"] = saveSettings;
    newDispatch["settings"] = saveSettings;
    newDispatch["notifications"] = saveSettings;
    newDispatch["storage"] = saveLocalStorage;
    setDispatch(newDispatch);
  }, [saveSettings, saveLocalStorage]);

  const submit = useCallback(() => {
    const maps = new Map<string, LooseObject>();

    // Separate settings by key
    for (const key in stagedChange) {
      const keys = key.split("-");
      if (maps.has(keys[0])) {
        const object = maps.get(keys[0])!;
        object[key] = stagedChange[key];
      } else {
        maps.set(keys[0], { [key]: stagedChange[key] });
      }
    }

    maps.forEach((v, k) => {
      if (k in dispatch) {
        dispatch[k](v);
      }
    });
  }, [stagedChange, dispatch]);

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
