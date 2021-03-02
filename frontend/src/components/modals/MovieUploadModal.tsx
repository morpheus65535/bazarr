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
import { useGetLanguage, useLanguages, useProfileBy } from "../../utilites";
import BaseModal, { BaseModalProps } from "./BaseModal";
interface MovieProps {
  update: (id: number) => void;
}

const MovieUploadModal: FunctionComponent<MovieProps & BaseModalProps> = (
  props
) => {
  const { update, ...modal } = props;

  const avaliableLanguages = useLanguages(true);

  const movie = usePayload<Item.Movie>(modal.modalKey);

  const closeModal = useCloseModal();

  const [uploading, setUpload] = useState(false);

  const [language, setLanguage] = useState<Language | undefined>(undefined);

  const profile = useProfileBy(movie?.profileId);

  const languageGetter = useGetLanguage(true);

  useWhenModalShow(modal.modalKey, () => {
    if (profile) {
      const first = profile.items[0]?.language;
      const lang = languageGetter(first);
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
    <BaseModal
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
    </BaseModal>
  );
};

export default connect(undefined, { update: movieUpdateInfoAll })(
  MovieUploadModal
);
