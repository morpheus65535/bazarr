import React, { FunctionComponent, useEffect, useMemo, useState } from "react";
import { Button, Container, Form } from "react-bootstrap";
import { FileForm, LanguageSelector } from "..";
import BackgroundTask from "../../@modules/task";
import { useIsGroupTaskRunning } from "../../@modules/task/hooks";
import { createTask } from "../../@modules/task/utilites";
import {
  useEnabledLanguages,
  useLanguageBy,
  useProfileBy,
} from "../../@redux/hooks";
import { MoviesApi } from "../../apis";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useModalInformation } from "./hooks";

export const TaskGroupName = "Uploading Movie Subtitles...";

const MovieUploadModal: FunctionComponent<BaseModalProps> = (props) => {
  const modal = props;

  const availableLanguages = useEnabledLanguages();

  const { payload, closeModal } = useModalInformation<Item.Movie>(
    modal.modalKey
  );

  const [language, setLanguage] = useState<Nullable<Language.Info>>(null);

  const profile = useProfileBy(payload?.profileId);

  const defaultLanguage = useLanguageBy(profile?.items[0]?.language);

  useEffect(() => setLanguage(defaultLanguage ?? null), [defaultLanguage]);

  const [file, setFile] = useState<Nullable<File>>(null);
  const [forced, setForced] = useState(false);

  const hasTask = useIsGroupTaskRunning(TaskGroupName);

  const canUpload = useMemo(() => {
    return file !== null && language?.code2 && !hasTask;
  }, [language, file, hasTask]);

  const footer = (
    <Button
      disabled={!canUpload}
      onClick={() => {
        if (file && payload && language) {
          const id = payload.radarrId;
          const task = createTask(
            file.name,
            id,
            MoviesApi.uploadSubtitles.bind(MoviesApi),
            id,
            {
              file: file,
              forced,
              hi: false,
              language: language.code2,
            }
          );
          BackgroundTask.dispatch(TaskGroupName, [task]);
          closeModal(props.modalKey);
        }
      }}
    >
      Upload
    </Button>
  );

  return (
    <BaseModal title={`Upload - ${payload?.title}`} footer={footer} {...modal}>
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
