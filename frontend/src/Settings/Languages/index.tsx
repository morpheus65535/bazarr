import React from "react";
import { Container } from "react-bootstrap";
import { connect } from "react-redux";
import {} from "../../redux/actions/system";

import TitleBlock from "../../components/TitleBlock";
import { CommonHeader, CommonHeaderBtn } from "../../components/CommonHeader";

import { faSave } from "@fortawesome/free-solid-svg-icons";

interface Props {
  languages: Array<Language>;
  enabled: Array<Language>;
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.languages.items,
    enabled: system.enabledLanguage,
  };
}

class SettingsLanguages extends React.Component<Props, {}> {
  render(): JSX.Element {
    const subtitles: JSX.Element = (
      <TitleBlock title="Subtitles Languages">
        <span></span>
      </TitleBlock>
    );

    const defaultSetting: JSX.Element = (
      <TitleBlock title="Default Settings">
        <span></span>
      </TitleBlock>
    );

    return (
      <Container fluid className="p-0">
        <CommonHeader>
          <CommonHeaderBtn
            iconProps={{ icon: faSave }}
            text="Save"
          ></CommonHeaderBtn>
        </CommonHeader>
        <div className="p-3">
          {subtitles}
          {defaultSetting}
        </div>
      </Container>
    );
  }
}

export default connect(mapStateToProps, {})(SettingsLanguages);
