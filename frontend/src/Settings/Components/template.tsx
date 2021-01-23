import React, { FunctionComponent, useCallback, useState } from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import {
  ContentHeader,
  ContentHeaderButton,
  AsyncStateOverlay,
} from "../../Components";

import { faSave } from "@fortawesome/free-solid-svg-icons";

import { SystemApi } from "../../apis";

import { UpdateAfterSettings } from "../../@redux/actions";

interface Props {
  title: string;
  settings: AsyncState<SystemSettings | undefined>;
  update: () => void;
  children: (
    settings: SystemSettings,
    update: (v: any, k?: string) => void,
    change: LooseObject
  ) => JSX.Element;
}

function mapStateToProps({ system }: StoreState) {
  return {
    settings: system.settings,
  };
}

const SettingsSubtitlesView: FunctionComponent<Props> = (props) => {
  const { settings, children, title, update } = props;

  const [willChange, setWillChange] = useState<LooseObject>({});

  const [updating, setUpdating] = useState(false);

  const updateChange = useCallback(
    (v: any, k?: string) => {
      if (k) {
        willChange[k] = v;

        if (process.env.NODE_ENV === "development") {
          console.log("stage settings", willChange);
        }
        setWillChange({ ...willChange });
      }
    },
    [willChange]
  );

  const submit = useCallback(() => {
    setUpdating(true);
    SystemApi.setSettings(willChange).finally(() => {
      setWillChange({});
      setUpdating(false);
      update();
    });
  }, [willChange]);

  return (
    <AsyncStateOverlay state={settings}>
      {(item) => (
        <Container fluid>
          <Helmet>
            <title>{title}</title>
          </Helmet>
          <ContentHeader>
            <ContentHeaderButton
              icon={faSave}
              updating={updating}
              disabled={Object.keys(willChange).length === 0}
              onClick={submit}
            >
              Save
            </ContentHeaderButton>
          </ContentHeader>
          <Row className="p-4">{children(item, updateChange, willChange)}</Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: UpdateAfterSettings })(
  SettingsSubtitlesView
);
