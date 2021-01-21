import React from "react";
import { connect } from "react-redux";
import { Container, Form } from "react-bootstrap";

import BasicModal, { ModalProps } from "./BasicModal";

import { LanguageSelector, Selector, AsyncButton } from "../";

import { forcedOptions } from "../../utilites/global";

interface Props {
  languages: ExtendLanguage[];
  item?: ExtendItem;
  submit: (form: ItemModifyForm) => Promise<void>;
  onSuccess?: () => void;
}

interface State {
  updating: boolean;
  changed: boolean;
  enabled: ExtendLanguage[];
  hi: boolean;
  forced: ForcedOptions;
}

function mapStateToProps({ system }: StoreState) {
  return {
    languages: system.enabledLanguage,
  };
}

class Editor extends React.Component<Props & ModalProps, State> {
  constructor(props: Props & ModalProps) {
    super(props);

    this.state = {
      enabled:
        props.item?.languages.map((val) => {
          return {
            ...val,
            enabled: true,
          };
        }) ?? [],
      hi: props.item?.hearing_impaired ?? false,
      forced: props.item?.forced ?? "False",
      changed: false,
      updating: false,
    };
  }

  updateState<K extends keyof State>(key: K, value: State[K]) {
    let state: State = {
      ...this.state,
      changed: true,
    };
    state[key] = value;
    this.setState(state);
  }

  submitForm() {
    const { submit } = this.props;
    const { enabled, hi, forced } = this.state;

    return submit({
      languages: enabled.map((val) => val.code2 ?? ""),
      hi,
      forced,
    });
  }

  render() {
    const { item, languages, onSuccess } = this.props;

    const { changed, enabled, hi, forced, updating } = this.state;

    const footer = (
      <AsyncButton
        disabled={!changed}
        onChange={(v) => this.updateState("updating", v)}
        promise={this.submitForm.bind(this)}
        success={onSuccess}
      >
        Save
      </AsyncButton>
    );

    return (
      <BasicModal closeable={!updating} {...this.props} footer={footer}>
        <Container fluid>
          <Form>
            <Form.Group>
              <Form.Label>Audio</Form.Label>
              <Form.Control
                type="text"
                disabled
                defaultValue={item?.audio_language.name}
              ></Form.Control>
            </Form.Group>
            <Form.Group>
              <Form.Label>Languages</Form.Label>
              <LanguageSelector
                multiple
                options={languages}
                defaultSelect={enabled}
                onChange={(val: ExtendLanguage[]) =>
                  this.updateState("enabled", val)
                }
              ></LanguageSelector>
            </Form.Group>
            <Form.Group>
              <Form.Label>Forced</Form.Label>
              <Selector
                options={forcedOptions}
                defaultKey={forced}
                onSelect={(val: string) =>
                  this.updateState("forced", val as ForcedOptions)
                }
              ></Selector>
            </Form.Group>
            <Form.Group>
              <Form.Check
                inline
                label="Hearing Impaired"
                defaultChecked={hi}
                onChange={(e) => {
                  this.updateState("hi", e.currentTarget.checked);
                }}
              ></Form.Check>
            </Form.Group>
          </Form>
        </Container>
      </BasicModal>
    );
  }
}

export default connect(mapStateToProps)(Editor);
