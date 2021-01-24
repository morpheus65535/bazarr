import React, { FunctionComponent, useEffect, useMemo, useState } from "react";
import { RouteComponentProps, withRouter } from "react-router-dom";
import { connect } from "react-redux";
import { Helmet } from "react-helmet";

import { Container, Row } from "react-bootstrap";

import { faHdd, faAdjust } from "@fortawesome/free-solid-svg-icons";

import {
  faSync,
  faSearch,
  faCloudUploadAlt,
  faWrench,
} from "@fortawesome/free-solid-svg-icons";

import { updateSeriesInfo } from "../../@redux/actions";

import {
  ContentHeader,
  ContentHeaderButton,
  ContentHeaderGroup,
  ItemOverview,
  ItemEditorModal,
  SeriesUploadModal,
  LoadingIndicator,
} from "../../components";

import { SeriesApi } from "../../apis";

import Table from "./table";

interface Params {
  id: string;
}

interface Props extends RouteComponentProps<Params> {
  seriesList: AsyncState<Series[]>;
  update: (id: number) => void;
}

function mapStateToProps({ series }: StoreState) {
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

  const [modal, setModal] = useState("");
  const [scan, setScan] = useState(false);
  const [search, setSearch] = useState(false);

  useEffect(() => {
    update(id);
  }, [update, id]);

  const header = (
    <ContentHeader>
      <ContentHeaderGroup pos="start">
        <ContentHeaderButton
          icon={faSync}
          updating={scan}
          onClick={() => {
            setScan(true);
            SeriesApi.scanDisk(id).finally(() => {
              setScan(false);
              update(id);
            });
          }}
        >
          Scan Disk
        </ContentHeaderButton>
        <ContentHeaderButton
          icon={faSearch}
          updating={search}
          onClick={() => {
            setSearch(true);
            SeriesApi.searchMissing(id).finally(() => {
              setSearch(false);
              update(id);
            });
          }}
        >
          Search
        </ContentHeaderButton>
      </ContentHeaderGroup>
      <ContentHeaderGroup pos="end">
        <ContentHeaderButton
          disabled={item?.episodeFileCount === 0 ?? false}
          icon={faCloudUploadAlt}
          onClick={() => setModal("upload")}
        >
          Upload
        </ContentHeaderButton>
        <ContentHeaderButton icon={faWrench} onClick={() => setModal("edit")}>
          Edit Series
        </ContentHeaderButton>
      </ContentHeaderGroup>
    </ContentHeader>
  );

  if (item) {
    return (
      <Container fluid>
        <Helmet>
          <title>{item.title} - Bazarr (Series)</title>
        </Helmet>
        {header}
        <Row>
          <ItemOverview item={item} details={details}></ItemOverview>
        </Row>
        <Row>
          <Table id={id}></Table>
        </Row>
        <ItemEditorModal
          show={modal === "edit"}
          item={item}
          onClose={() => setModal("")}
          submit={(form) => SeriesApi.modify(item.sonarrSeriesId, form)}
          onSuccess={() => {
            setModal("");
            update(item.sonarrSeriesId);
          }}
        ></ItemEditorModal>
        <SeriesUploadModal
          series={item}
          show={modal === "upload"}
          onClose={() => setModal("")}
        ></SeriesUploadModal>
      </Container>
    );
  } else {
    return <LoadingIndicator></LoadingIndicator>;
  }
};

export default withRouter(
  connect(mapStateToProps, { update: updateSeriesInfo })(SeriesEpisodesView)
);
