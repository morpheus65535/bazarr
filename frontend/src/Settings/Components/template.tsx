import React, { FunctionComponent, useState } from "react";
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

interface Props {
  title: string;
  settings: AsyncState<SystemSettings | undefined>;
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
  const { settings, children, title } = props;

  const [willChange, setWillChange] = useState<LooseObject>({});

  function updateChange(v: any, k?: string) {
    if (k) {
      willChange[k] = v;
      setWillChange(Object.assign({}, willChange));
    }
  }

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
              disabled={Object.keys(willChange).length === 0}
              onClick={() => {
                SystemApi.setSettings(willChange);
                setWillChange({});
              }}
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

export default connect(mapStateToProps)(SettingsSubtitlesView);
