import { createReducer } from "@reduxjs/toolkit";
import { hideModalAction, showModalAction } from "../actions/modal";

interface ModalReducer {
  stack: Modal.Frame[];
}

const reducer = createReducer<ModalReducer>({ stack: [] }, (builder) => {
  builder.addCase(showModalAction, (state, action) => {
    state.stack.push(action.payload);
  });

  builder.addCase(hideModalAction, (state, action) => {
    state.stack = state.stack.filter((frame) => frame.key !== action.payload);
  });
});

export default reducer;
