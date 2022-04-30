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
    const { payload } = action;
    if (payload === undefined) {
      state.stack.pop();
    } else {
      const index = state.stack.findIndex((fr) => fr.key === payload);
      if (index !== -1) {
        state.stack.splice(index);
      }
    }
  });
});

export default reducer;
