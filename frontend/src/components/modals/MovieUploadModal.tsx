import React, { FunctionComponent, useEffect, useMemo, useState } from "react";
import { Container, Form } from "react-bootstrap";
import {
  AsyncButton,
  FileForm,
  LanguageSelector,
  useCloseModal,
  usePayload,
} from "..";
import { useLanguageBy, useLanguages, useProfileBy } from "../../@redux/hooks";
import { MoviesApi } from "../../apis";
import BaseModal, { BaseModalProps } from "./BaseModal";
interface MovieProps {}

const MovieUploadModal: FunctionComponent<MovieProps & BaseModalProps> = (
  props
) => {
  const modal = props;

  const [availableLanguages] = useLanguages(true);

  const movie = usePayload<Item.Movie>(modal.modalKey);

  const closeModal = useCloseModal();

  const [uploading, setUpload] = useState(false);

  const [language, setLanguage] = useState<Nullable<Language>>(null);

  const profile = useProfileBy(movie?.profileId);

  const defaultLanguage = useLanguageBy(profile?.items[0]?.language);

  useEffect(() => setLanguage(defaultLanguage ?? null), [defaultLanguage]);

  const [file, setFile] = useState<Nullable<File>>(null);
  const [forced, setForced] = useState(false);

  const canUpload = useMemo(() => {
    return file !== null && language?.code2;
  }, [language, file]);

  const footer = (
    <AsyncButton
      noReset
      disabled={!canUpload}
      onChange={setUpload}
      promise={() => {
        if (file && movie && language) {
          return MoviesApi.uploadSubtitles(movie.radarrId, {
            file: file,
            forced,
            hi: false,
            language: language.code2,
          });
        } else {
          return null;
        }
      }}
      onSuccess={closeModal}
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
              options={availableLanguages}
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

export default MovieUploadModal;
