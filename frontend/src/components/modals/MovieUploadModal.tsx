import { faTrash } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, {
  FunctionComponent,
  useCallback,
  useMemo,
  useState,
} from "react";
import { Button, Container, Form } from "react-bootstrap";
import { Column, Row } from "react-table";
import { dispatchTask } from "../../@modules/task";
import { createTask } from "../../@modules/task/utilites";
import { useProfileBy, useProfileItemsToLanguages } from "../../@redux/hooks";
import { MoviesApi } from "../../apis";
import { BuildKey } from "../../utilites";
import { FileForm } from "../inputs";
import { LanguageSelector } from "../LanguageSelector";
import { SimpleTable } from "../tables";
import BaseModal, { BaseModalProps } from "./BaseModal";
import { useModalInformation } from "./hooks";

interface PendingSubtitle {
  file: File;
  language: Language.Info;
  forced: boolean;
}

export const TaskGroupName = "Uploading Subtitles...";

const MovieUploadModal: FunctionComponent<BaseModalProps> = (props) => {
  const modal = props;

  const { payload, closeModal } = useModalInformation<Item.Movie>(
    modal.modalKey
  );

  const profile = useProfileBy(payload?.profileId);

  const availableLanguages = useProfileItemsToLanguages(profile);

  const [pending, setPending] = useState<PendingSubtitle[]>([]);

  const filelist = useMemo(() => pending.map((v) => v.file), [pending]);

  const setFiles = useCallback(
    (files: File[]) => {
      const list: PendingSubtitle[] = files.map((v) => ({
        file: v,
        forced: availableLanguages[0].forced ?? false,
        language: availableLanguages[0],
      }));
      setPending(list);
    },
    [availableLanguages]
  );

  const upload = useCallback(() => {
    if (payload === null || pending.length === 0) {
      return;
    }

    const { radarrId } = payload;

    const tasks = pending.map((v) => {
      const { file, language, forced } = v;

      return createTask(
        file.name,
        radarrId,
        MoviesApi.uploadSubtitles.bind(MoviesApi),
        radarrId,
        {
          file: file,
          forced,
          hi: false,
          language: language.code2,
        }
      );
    });

    dispatchTask(TaskGroupName, tasks, "Uploading...");
    setFiles([]);
    closeModal();
  }, [payload, closeModal, pending, setFiles]);

  const modify = useCallback(
    (row: Row<PendingSubtitle>, info?: PendingSubtitle) => {
      setPending((pd) => {
        const newPending = [...pd];
        if (info) {
          newPending[row.index] = info;
        } else {
          newPending.splice(row.index, 1);
        }
        return newPending;
      });
    },
    []
  );

  const columns = useMemo<Column<PendingSubtitle>[]>(
    () => [
      {
        id: "name",
        Header: "File",
        accessor: (d) => d.file.name,
      },
      {
        Header: "Forced",
        accessor: "forced",
        Cell: ({ row, value, update }) => {
          const { original, index } = row;
          return (
            <Form.Check
              custom
              id={BuildKey(index, original.file.name, "forced")}
              checked={value}
              onChange={(v) => {
                const newInfo = { ...row.original };
                newInfo.forced = v.target.checked;
                update && update(row, newInfo);
              }}
            ></Form.Check>
          );
        },
      },
      {
        Header: "Language",
        accessor: "language",
        className: "w-25",
        Cell: ({ row, update, value }) => {
          return (
            <LanguageSelector
              options={availableLanguages}
              value={value}
              onChange={(lang) => {
                if (lang && update) {
                  const newInfo = { ...row.original };
                  newInfo.language = lang;
                  update(row, newInfo);
                }
              }}
            ></LanguageSelector>
          );
        },
      },
      {
        accessor: "file",
        Cell: ({ row, update }) => {
          return (
            <Button
              size="sm"
              variant="light"
              onClick={() => {
                update && update(row);
              }}
            >
              <FontAwesomeIcon icon={faTrash}></FontAwesomeIcon>
            </Button>
          );
        },
      },
    ],
    [availableLanguages]
  );

  const canUpload = pending.length > 0;

  const footer = (
    <Button disabled={!canUpload} onClick={upload}>
      Upload
    </Button>
  );

  return (
    <BaseModal title={`Upload - ${payload?.title}`} footer={footer} {...modal}>
      <Container fluid className="flex-column">
        <Form>
          <Form.Group>
            <FileForm
              emptyText="Select..."
              disabled={canUpload || availableLanguages.length === 0}
              multiple
              value={filelist}
              onChange={setFiles}
            ></FileForm>
          </Form.Group>
        </Form>
        <div hidden={!canUpload}>
          <SimpleTable
            columns={columns}
            data={pending}
            responsive={false}
            update={modify}
          ></SimpleTable>
        </div>
      </Container>
    </BaseModal>
  );
};

export default MovieUploadModal;
