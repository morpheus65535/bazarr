import { faSave } from "@fortawesome/free-solid-svg-icons";
import { merge } from "lodash";
import React, {
  FunctionComponent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { Prompt } from "react-router";
import { useDidUpdate } from "rooks";
import { useSystemSettings } from "../../@redux/hooks";
import { useUpdateLocalStorage } from "../../@storage/local";
import { SystemApi } from "../../apis";
import { ContentHeader } from "../../components";
import { log } from "../../utilities/logger";
import {
  enabledLanguageKey,
  languageProfileKey,
  notificationsKey,
} from "../keys";

type SettingDispatcher = Record<string, (settings: LooseObject) => void>;

export const StagedChangesContext = React.createContext<
  SimpleStateType<LooseObject>
>([{}, () => {}]);

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
  title: string;
  children: JSX.Element | JSX.Element[];
}

const SettingsProvider: FunctionComponent<Props> = (props) => {
  const { children, title } = props;

  const updateStorage = useUpdateLocalStorage();

  const [stagedChange, setChange] = useState<LooseObject>({});
  const [updating, setUpdating] = useState(false);
  const [dispatcher, setDispatcher] = useState<SettingDispatcher>({});

  const settings = useSystemSettings();
  useDidUpdate(() => {
    // Will be updated by websocket
    if (settings.state !== "loading") {
      setChange({});
      setUpdating(false);
    }
  }, [settings.state]);

  const saveSettings = useCallback((settings: LooseObject) => {
    submitHooks(settings);
    setUpdating(true);
    log("info", "submitting settings", settings);
    SystemApi.setSettings(settings);
  }, []);

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
      <StagedChangesContext.Provider value={[stagedChange, setChange]}>
        <Row className="p-4">
          <Container>{children}</Container>
        </Row>
      </StagedChangesContext.Provider>
    </Container>
  );
};

export default SettingsProvider;
