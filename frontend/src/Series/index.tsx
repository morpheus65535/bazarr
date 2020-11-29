import React from "react";
import { connect } from "react-redux";
import { Container } from "react-bootstrap";
import { faList } from "@fortawesome/free-solid-svg-icons";

import ContentHeader, {
  ContentHeaderButton,
} from "../components/ContentHeader";
import Table from "./table";
import ItemSimpleEditor from "../components/EditItemModal";

interface Props {}

interface State {
  modal?: Series;
}

function mapStateToProps({ series }: StoreState) {
  return {};
}

class SeriesView extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      modal: undefined,
    };
  }

  onSeriesEditClick(series: Series) {
    this.setState({
      ...this.state,
      modal: series,
    });
  }

  onSeriesEditorClose() {
    this.setState({
      ...this.state,
      modal: undefined,
    });
  }

  render(): JSX.Element {
    const { modal } = this.state;

    return (
      <Container fluid className="px-0">
        <ContentHeader>
          <ContentHeaderButton iconProps={{ icon: faList }}>
            Mass Edit
          </ContentHeaderButton>
        </ContentHeader>
        <div className="p-3">
          <Table openSeriesEditor={this.onSeriesEditClick.bind(this)}></Table>
        </div>
        <ItemSimpleEditor
          item={modal}
          close={this.onSeriesEditorClose.bind(this)}
        ></ItemSimpleEditor>
      </Container>
    );
  }
}

export default connect(mapStateToProps)(SeriesView);
