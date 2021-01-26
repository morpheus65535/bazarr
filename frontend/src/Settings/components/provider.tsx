import React, {
  FunctionComponent,
  useCallback,
  useContext,
  useState,
} from "react";
import { Prompt } from "react-router";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { AsyncStateOverlay, ContentHeader } from "../../components";

import { faSave } from "@fortawesome/free-solid-svg-icons";

import { SystemApi } from "../../apis";

import { UpdateSettingsRelative } from "../../@redux/actions";

import { enabledLanguageKey, languageProfileKey } from "../keys";

type UpdateFunctionType = (v: any, k?: string) => void;

const UpdateChangeContext = React.createContext<
  [LooseObject, UpdateFunctionType]
>([{}, (v: any, k?: string) => {}]);

const SettingsContext = React.createContext<SystemSettings | undefined>(
  undefined
);

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
  return useContext(UpdateChangeContext)[1];
}

export function useStaged(): LooseObject {
  return useContext(UpdateChangeContext)[0];
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
}

function mapStateToProps({ system }: StoreState) {
  return {
    settings: system.settings,
  };
}

interface Props {
  title: string;
  settings: AsyncState<SystemSettings | undefined>;
  update: () => void;
  children: JSX.Element | JSX.Element[];
}

const SettingsProvider: FunctionComponent<Props> = (props) => {
  const { settings, children, title, update } = props;

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
    <AsyncStateOverlay state={settings}>
      {(items) => (
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
          <SettingsContext.Provider value={items}>
            <UpdateChangeContext.Provider value={[stagedChange, updateChange]}>
              <Row className="p-4">
                <Container>{children}</Container>
              </Row>
            </UpdateChangeContext.Provider>
          </SettingsContext.Provider>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: UpdateSettingsRelative })(
  SettingsProvider
);
