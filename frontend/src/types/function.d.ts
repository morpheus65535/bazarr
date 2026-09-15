type RangeQuery<T> = (
  param: Parameter.ListQuery,
) => Promise<DataWrapperWithTotal<T>>;
