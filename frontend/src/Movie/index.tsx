import React from "react";
import { connect } from "react-redux";

class MovieView extends React.Component {
    render() {
        return <span>Movie</span>
    }
}

export default connect()(MovieView);