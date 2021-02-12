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
import { connect } from "react-redux";
import { Prompt } from "react-router";
import {
  siteSaveLocalstorage,
  systemUpdateSettingsAll,
} from "../../@redux/actions";
import { SystemApi } from "../../apis";
import { ContentHeader } from "../../components";
import {
  enabledLanguageKey,
  languageProfileKey,
  notificationsKey,
} from "../keys";
import { SettingsContext } from "../Router";

export type UpdateFunctionType = (v: any, k?: string) => void;

export const UpdateChangeContext = React.createContext<UpdateFunctionType>(
  (v: any, k?: string) => {}
);

export const StagedChangesContext = React.createContext<LooseObject>({});

export function useSettings(): SystemSettings {
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
    const item = settings[notificationsKey] as NotificationInfo[];
    settings[notificationsKey] = item.map((v) => JSON.stringify(v));
  }
}

type SettingDispatch = Record<string, (settings: LooseObject) => void>;

interface Props {
  title: string;
  update: () => void;
  updateLocal: (settings: LooseObject) => void;
  children: JSX.Element | JSX.Element[];
}

const SettingsProvider: FunctionComponent<Props> = (props) => {
  const { children, title, update, updateLocal } = props;

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
      updateLocal(settings);
      setChange({});
    },
    [updateLocal]
  );

  useEffect(() => {
    // Update dispatch
    const newDispatch: SettingDispatch = {};
    newDispatch["settings"] = saveSettings;
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
      <UpdateChangeContext.Provider value={updateChange}>
        <StagedChangesContext.Provider value={stagedChange}>
          <Row className="p-4">
            <Container>{children}</Container>
          </Row>
        </StagedChangesContext.Provider>
      </UpdateChangeContext.Provider>
    </Container>
  );
};

export default connect(undefined, {
  update: systemUpdateSettingsAll,
  updateLocal: siteSaveLocalstorage,
})(SettingsProvider);
