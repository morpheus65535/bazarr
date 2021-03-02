import {
  faAdjust,
  faCloudUploadAlt,
  faHdd,
  faSearch,
  faSync,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";
import React, { FunctionComponent, useEffect, useMemo } from "react";
import { Container, Row } from "react-bootstrap";
import { Helmet } from "react-helmet";
import { connect } from "react-redux";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { seriesUpdateInfoAll } from "../../@redux/actions";
import { SeriesApi } from "../../apis";
import {
  ContentHeader,
  ItemEditorModal,
  ItemOverview,
  LoadingIndicator,
  SeriesUploadModal,
  useShowModal,
} from "../../components";
import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Item.Series[]>;
  update: (id: number) => void;
}

function mapStateToProps({ series }: ReduxStore) {
  const { seriesList } = series;
  return {
    seriesList,
  };
}

const SeriesEpisodesView: FunctionComponent<Props> = (props) => {
  const { update, match, seriesList } = props;
  const id = Number.parseInt(match.params.id);
  const list = seriesList.items;

  const item = useMemo(() => list.find((val) => val.sonarrSeriesId === id), [
    list,
    id,
  ]);

  const details = useMemo(
    () => [
      {
        icon: faHdd,
        text: `${item?.episodeFileCount} files`,
      },
      {
        icon: faAdjust,
        text: item?.seriesType ?? "",
      },
    ],
    [item]
  );

  const showModal = useShowModal();

  useEffect(() => {
    update(id);
  }, [update, id]);

  if (!item) {
    return <LoadingIndicator></LoadingIndicator>;
  }

  return (
    <Container fluid>
      <Helmet>
        <title>{item.title} - Bazarr (Series)</title>
      </Helmet>
      <ContentHeader>
        <ContentHeader.Group pos="start">
          <ContentHeader.AsyncButton
            icon={faSync}
            promise={() =>
              SeriesApi.action({ action: "scan-disk", seriesid: id })
            }
            onSuccess={() => update(id)}
          >
            Scan Disk
          </ContentHeader.AsyncButton>
          <ContentHeader.AsyncButton
            icon={faSearch}
            promise={() =>
              SeriesApi.action({ action: "search-missing", seriesid: id })
            }
            onSuccess={() => update(id)}
            disabled={item.episodeFileCount === 0 || item.profileId === null}
          >
            Search
          </ContentHeader.AsyncButton>
        </ContentHeader.Group>
        <ContentHeader.Group pos="end">
          <ContentHeader.Button
            disabled={item.episodeFileCount === 0 || item.profileId === null}
            icon={faCloudUploadAlt}
            onClick={() => showModal("upload", item)}
          >
            Upload
          </ContentHeader.Button>
          <ContentHeader.Button
            icon={faWrench}
            onClick={() => showModal("edit", item)}
          >
            Edit Series
          </ContentHeader.Button>
        </ContentHeader.Group>
      </ContentHeader>
      <Row>
        <ItemOverview item={item} details={details}></ItemOverview>
      </Row>
      <Row>
        <Table series={item}></Table>
      </Row>
      <ItemEditorModal
        modalKey="edit"
        submit={(form) => SeriesApi.modify(form)}
        onSuccess={(item) => update((item as Item.Series).sonarrSeriesId)}
      ></ItemEditorModal>
      <SeriesUploadModal modalKey="upload"></SeriesUploadModal>
    </Container>
  );
};

export default withRouter(
  connect(mapStateToProps, { update: seriesUpdateInfoAll })(SeriesEpisodesView)
);
