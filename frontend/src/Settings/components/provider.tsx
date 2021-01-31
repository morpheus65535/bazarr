import { faSave } from "@fortawesome/free-solid-svg-icons";
import React, {
  FunctionComponent,
  useCallback,
  useContext,
  useState,
} from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { Prompt } from "react-router";
import { systemUpdateSettingsAll } from "../../@redux/actions";
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

interface Props {
  title: string;
  update: () => void;
  children: JSX.Element | JSX.Element[];
}

const SettingsProvider: FunctionComponent<Props> = (props) => {
  const { children, title, update } = props;

  const [stagedChange, setChange] = useState<LooseObject>({});

  const [updating, setUpdating] = useState(false);

  const updateChange = useCallback<UpdateFunctionType>(
    (v: any, k?: string) => {
      if (k) {
        stagedChange[k] = v;

        if (process.env.NODE_ENV === "development") {
          console.log("stage settings", stagedChange);
        }
        setChange({ ...stagedChange });
      }
    },
    [stagedChange]
  );

  const submit = useCallback(() => {
    const newSettings = { ...stagedChange };
    beforeSubmit(newSettings);
    setUpdating(true);
    console.log("submitting settings", newSettings);
    SystemApi.setSettings(newSettings).finally(() => {
      update();
      setChange({});
      setUpdating(false);
    });
  }, [stagedChange, update]);

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

export default connect(undefined, { update: systemUpdateSettingsAll })(
  SettingsProvider
);
