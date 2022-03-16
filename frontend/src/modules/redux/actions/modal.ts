import { createAction } from "@reduxjs/toolkit";

export const showModalAction = createAction<Modal.Frame>("modal/show");

export const hideModalAction = createAction<string | undefined>("modal/hide");
