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

import { SetSystemSettings } from "../../@redux/actions";

interface Props {
  title: string;
  settings: AsyncState<SystemSettings | undefined>;
  children: (
    settings: SystemSettings,
    update: (v: any, k?: string) => void
  ) => JSX.Element;
  update: (data: object) => void;
}

function mapStateToProps({ system }: StoreState) {
  return {
    settings: system.settings,
  };
}

const SettingsSubtitlesView: FunctionComponent<Props> = (props) => {
  const { settings, children, title, update } = props;

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
          <Row>
            <ContentHeader>
              <ContentHeaderButton
                icon={faSave}
                disabled={Object.keys(willChange).length === 0}
                onClick={() => {
                  update(willChange);
                  setWillChange({});
                }}
              >
                Save
              </ContentHeaderButton>
            </ContentHeader>
          </Row>
          <Row>{children(item, updateChange)}</Row>
        </Container>
      )}
    </AsyncStateOverlay>
  );
};

export default connect(mapStateToProps, { update: SetSystemSettings })(
  SettingsSubtitlesView
);
