import React, { FunctionComponent, useMemo, useState } from "react";
import { Container, Form } from "react-bootstrap";
import { connect } from "react-redux";
import {
  AsyncButton,
  FileForm,
  LanguageSelector,
  useCloseModal,
  usePayload,
  useWhenModalShow,
} from "..";
import { movieUpdateInfoAll } from "../../@redux/actions";
import { MoviesApi } from "../../apis";
import BasicModal, { BasicModalProps } from "./BasicModal";
interface MovieProps {
  avaliableLanguages: Language[];
  update: (id: number) => void;
}

function mapStateToProps({ system }: StoreState) {
  return {
    avaliableLanguages: system.enabledLanguage.items,
  };
}

const MovieUploadModal: FunctionComponent<MovieProps & BasicModalProps> = (
  props
) => {
  const { avaliableLanguages, update, ...modal } = props;

  const movie = usePayload<Movie>(modal.modalKey);

  const closeModal = useCloseModal();

  const [uploading, setUpload] = useState(false);

  const [language, setLanguage] = useState<Language | undefined>(undefined);

  useWhenModalShow(modal.modalKey, () => {
    if (movie) {
      const lang = movie.languages.length > 0 ? movie.languages[0] : undefined;
      setLanguage(lang);
    }
  });

  const [file, setFile] = useState<File | undefined>(undefined);
  const [forced, setForced] = useState(false);

  const canUpload = useMemo(() => {
    return file !== undefined && language?.code2 !== undefined;
  }, [language, file]);

  const footer = (
    <AsyncButton
      disabled={!canUpload}
      onChange={setUpload}
      promise={() =>
        MoviesApi.uploadSubtitles(movie!.radarrId, {
          file: file!,
          forced,
          hi: false,
          language: language!.code2!,
        })
      }
      onSuccess={() => {
        closeModal();
        if (movie) {
          update(movie.radarrId);
        }
      }}
    >
      Upload
    </AsyncButton>
  );

  return (
    <BasicModal
      title={`Upload - ${movie?.title}`}
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
              value={language}
              onChange={(lang) => {
                if (lang) {
                  setLanguage(lang);
                }
              }}
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
              custom
              id="forced-checkbox"
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

export default connect(mapStateToProps, { update: movieUpdateInfoAll })(
  MovieUploadModal
);
