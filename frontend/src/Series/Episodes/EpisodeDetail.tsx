import React, { FunctionComponent } from "react"

import { Image, Container, Row, Col, Badge } from "react-bootstrap";


interface Props {
    series: Series;
}

const EpisodeDetail: FunctionComponent<Props> = (props) => {
    const badgeClass = "mr-2";
    const infoRowClass = "mb-2";

    const { series } = props;

    let subtitleLanguages: JSX.Element[] = [];

    if (series.languages instanceof Array) {
      subtitleLanguages = series.languages.map((val) => {
        return (
          <Badge variant="secondary" className={badgeClass} key={val.name}>
            {val.name}
          </Badge>
        );
      });
    }

    return (
      <Container fluid className="p-4">
        <Row>
          <Col sm="auto">
            <Image src={series.poster}></Image>
          </Col>
          <Col>
            <Container fluid>
              <Row className={infoRowClass}>
                <h1>{series.title}</h1>
                {/* Tooltip */}
              </Row>
              <Row className={infoRowClass}>
                <Badge variant="secondary" className={badgeClass}>
                  {series.audio_language.name}
                </Badge>
                <Badge variant="secondary" className={badgeClass}>
                  {series.mapped_path}
                </Badge>
                <Badge variant="secondary" className={badgeClass}>
                  {series.episodeFileCount} files
                </Badge>
                <Badge variant="secondary" className={badgeClass}>
                  {series.seriesType}
                </Badge>
                <Badge variant="secondary" className={badgeClass}>
                  {/* TODO: Array */}
                  {series.tags}
                </Badge>
              </Row>
              <Row className={infoRowClass}>{subtitleLanguages}</Row>
              <Row className={infoRowClass}>
                <Badge variant="secondary" className={badgeClass}>
                  Hearing-Impaired: {series.hearing_impaired}
                </Badge>
                <Badge variant="secondary" className={badgeClass}>
                  Forced: {series.forced}
                </Badge>
              </Row>
              <Row className={infoRowClass}>
                <span>{series.overview}</span>
              </Row>
            </Container>
          </Col>
        </Row>
      </Container>
    );
}

export default EpisodeDetail;