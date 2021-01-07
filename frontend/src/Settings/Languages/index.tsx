import React from "react";
import { Container, Row } from "react-bootstrap";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import {
  AsyncStateOverlay,
  ContentHeader,
  ContentHeaderButton,
  LanguageSelector,
} from "../../Components";

import { Group, Message, Input, Check } from "../Components";

import { faSave } from "@fortawesome/free-solid-svg-icons";

interface Props {
  settings: AsyncState<SystemSettings | undefined>;
  languages: ExtendLanguage[];
  enabled: Array<ExtendLanguage>;
}

function mapStateToProps({ system }: StoreState) {
  return {
    settings: system.settings,
    languages: system.languages.items,
    enabled: system.enabledLanguage,
  };
}

class SettingsLanguagesView extends React.Component<Props> {
  render(): JSX.Element {
    const { settings, enabled, languages } = this.props;

    return (
      <AsyncStateOverlay state={settings}>
        {(item) => (
          <Container fluid>
            <Helmet>
              <title>Languages - Bazarr (Settings)</title>
            </Helmet>
            <Row>
              <ContentHeader>
                <ContentHeaderButton icon={faSave}>Save</ContentHeaderButton>
              </ContentHeader>
            </Row>
            <Row>
              <Container className="p-4">
                <Group header="Subtitles Language">
                  <Input>
                    <Check
                      label="Single Language"
                      defaultValue={item.general.single_language}
                    ></Check>
                    <Message type="info">
                      Download a single Subtitles file without adding the
                      language code to the filename.
                    </Message>
                    <Message type="warning">
                      We don't recommend enabling this option unless absolutely
                      required (ie: media player not supporting language code in
                      subtitles filename). Results may vary.
                    </Message>
                  </Input>
                  <Input name="Enabled Languages">
                    <LanguageSelector
                      className="px-0"
                      defaultSelect={enabled}
                      avaliable={languages}
                    ></LanguageSelector>
                  </Input>
                </Group>
                <Group header="Default Settings">
                  <Input>
                    <Check
                      label="Series"
                      defaultValue={item.general.serie_default_enabled}
                    ></Check>
                    <Message type="info">
                      Apply only to Series added to Bazarr after enabling this
                      option.
                    </Message>
                  </Input>
                  <Input>
                    <Check
                      label="Movies"
                      defaultValue={item.general.movie_default_enabled}
                    ></Check>
                    <Message type="info">
                      Apply only to Movies added to Bazarr after enabling this
                      option.
                    </Message>
                  </Input>
                </Group>
              </Container>
            </Row>
          </Container>
        )}
      </AsyncStateOverlay>
    );
  }
}

export default connect(mapStateToProps, {})(SettingsLanguagesView);
