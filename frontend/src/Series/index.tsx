import React from "react";
import { connect } from "react-redux";
import { Container } from "react-bootstrap";
import {CommonHeader, CommonHeaderBtn} from "../components/CommonHeader"

import { faList } from "@fortawesome/free-solid-svg-icons";

import { updateSeriesList } from "../redux/actions/series";

import Table from "./table";

interface Props {
  updateSeriesList: () => void;
}

class Series extends React.Component<Props, {}> {
  componentDidMount() {
    this.props.updateSeriesList();
  }
  render(): JSX.Element {
    return (
      <Container fluid className="px-0">
        <CommonHeader>
          <CommonHeaderBtn
            text="Mass Edit"
            iconProps={{ icon: faList}}
          ></CommonHeaderBtn>
        </CommonHeader>
        <div className="p-3">
          <Table></Table>
        </div>
      </Container>
    );
  }
}

export default connect(null, { updateSeriesList })(Series);
