import React from "react";
import { Container, Form } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import {
  SettingGroup,
  ContentHeader,
  ContentHeaderButton,
  CommonFormGroup,
  LanguageSelector,
} from "../../components";

import { faSave } from "@fortawesome/free-solid-svg-icons";

interface Props {
  languages: ExtendLanguage[];
  enabled: Array<ExtendLanguage>;
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.languages.items,
    enabled: system.enabledLanguage,
  };
}

class SettingsLanguagesView extends React.Component<Props, {}> {
  render(): JSX.Element {
    const { enabled, languages } = this.props;

    const subtitles: JSX.Element = (
      <SettingGroup name="Subtitles Languages">
        <CommonFormGroup title="Single Language">
          <Form.Check type="checkbox"></Form.Check>
          <Form.Label>
            Download a single Subtitles file without adding the language code to
            the filename.
          </Form.Label>
          <Form.Label className="text-warning">
            We don't recommend enabling this option unless absolutely required
            (ie: media player not supporting language code in subtitles
            filename). Results may vary.
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="Enabled Languages">
          <LanguageSelector
            className="px-0"
            enabled={enabled}
            languages={languages}
          ></LanguageSelector>
        </CommonFormGroup>
      </SettingGroup>
    );

    const defaultSetting: JSX.Element = (
      <SettingGroup name="Default Settings">
        <CommonFormGroup title="Series Default Settings">
          <Form.Check type="checkbox"></Form.Check>
          <Form.Label>
            Apply only to Series added to Bazarr after enabling this option.
          </Form.Label>
        </CommonFormGroup>
        <CommonFormGroup title="Movies Default Settings">
          <Form.Check type="checkbox"></Form.Check>
          <Form.Label>
            Apply only to Movies added to Bazarr after enabling this option.
          </Form.Label>
        </CommonFormGroup>
      </SettingGroup>
    );

    return (
      <Container fluid className="p-0">
        <Helmet>
          <title>Languages - Bazarr (Settings)</title>
        </Helmet>
        <ContentHeader>
          <ContentHeaderButton iconProps={{ icon: faSave }}>
            Save
          </ContentHeaderButton>
        </ContentHeader>
        <Form className="p-4">
          {subtitles}
          {defaultSetting}
        </Form>
      </Container>
    );
  }
}

export default connect(mapStateToProps, {})(SettingsLanguagesView);
