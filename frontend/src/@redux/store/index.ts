import { configureStore } from "@reduxjs/toolkit";
import reducer from "../reducers";

const store = configureStore({
  reducer,
});

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;

export default store;
