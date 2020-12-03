import React from "react";
import { Container } from "react-bootstrap";

import { connect } from "react-redux";
import { updateWantedSeriesList } from "../../@redux/actions/series";

import { faSearch } from "@fortawesome/free-solid-svg-icons";

import ContentHeader, {
  ContentHeaderButton,
} from "../../components/ContentHeader";

import Table from "./table";

interface Props {
  update: () => void;
}

class WantedSeriesView extends React.Component<Props> {
  componentDidMount() {
    this.props.update();
  }
  render(): JSX.Element {
    return (
      <Container fluid className="p-0">
        <ContentHeader>
          <ContentHeaderButton iconProps={{ icon: faSearch }}>
            Search All
          </ContentHeaderButton>
        </ContentHeader>
        <div className="p-3">
          <Table></Table>
        </div>
      </Container>
    );
  }
}

export default connect(null, {
  update: updateWantedSeriesList,
})(WantedSeriesView);
