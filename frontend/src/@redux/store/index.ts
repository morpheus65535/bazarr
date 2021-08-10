import { configureStore } from "@reduxjs/toolkit";
import apis from "../../apis";
import reducer from "../reducers";

const store = configureStore({
  reducer,
});

// FIXME
apis.dispatch = store.dispatch;

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;

export default store;
