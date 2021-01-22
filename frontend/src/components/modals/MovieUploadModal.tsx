import React, { FunctionComponent, useState, useMemo } from "react";
import { connect } from "react-redux";
import BasicModal, { ModalProps } from "./BasicModal";

import { AsyncButton, FileForm } from "..";

import { Container, Form } from "react-bootstrap";

import { MoviesApi } from "../../apis";
import { updateMovieInfo } from "../../@redux/actions";

import LanguageSelector from "../LanguageSelector";

interface MovieProps {
  movie: Movie;
  avaliableLanguages: ExtendLanguage[];
  update: (id: number) => void;
}

function mapStateToProps({ system }: StoreState) {
  return {
    avaliableLanguages: system.enabledLanguage,
  };
}

const MovieUploadModal: FunctionComponent<MovieProps & ModalProps> = (
  props
) => {
  const { movie, avaliableLanguages, update, ...modal } = props;

  const [uploading, setUpload] = useState(false);

  const [language, setLanguage] = useState<ExtendLanguage | undefined>(() => {
    const lang = movie.languages.length > 0 ? movie.languages[0] : undefined;
    if (lang) {
      return avaliableLanguages.find((v) => v.code2 === lang.code2);
    }

    return undefined;
  });
  const [file, setFile] = useState<File | undefined>(undefined);
  const [forced, setForced] = useState(movie.forced === "True");

  const canUpload = useMemo(() => {
    return file !== undefined && language?.code2 !== undefined;
  }, [language, file]);

  const footer = (
    <AsyncButton
      disabled={!canUpload}
      onChange={setUpload}
      promise={() =>
        MoviesApi.uploadSubtitles(movie.radarrId, {
          file: file!,
          forced,
          hi: movie.hearing_impaired,
          language: language!.code2!,
        })
      }
      success={() => {
        modal.onClose();
        update(movie.radarrId);
      }}
    >
      Upload
    </AsyncButton>
  );

  return (
    <BasicModal
      title={`Upload - ${movie.title}`}
      closeable={!uploading}
      footer={footer}
      {...modal}
    >
      <Container fluid>
        <Form>
          <Form.Group>
            <Form.Label>Language</Form.Label>
            <LanguageSelector
              options={avaliableLanguages}
              defaultSelect={language}
              onChange={setLanguage}
            ></LanguageSelector>
          </Form.Group>
          <Form.Group>
            <Form.Label>Subtitle File</Form.Label>
            <FileForm
              emptyText="Select..."
              onChange={(list) => {
                setFile(list[0]);
              }}
            ></FileForm>
          </Form.Group>
          <Form.Group>
            <Form.Check
              defaultChecked={forced}
              onChange={(e) => setForced(e.target.checked)}
              label="Forced"
            ></Form.Check>
          </Form.Group>
        </Form>
      </Container>
    </BasicModal>
  );
};

export default connect(mapStateToProps, { update: updateMovieInfo })(
  MovieUploadModal
);
