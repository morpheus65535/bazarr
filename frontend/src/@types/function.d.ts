type RangeQuery<T> = (
  param: Parameter.Range
) => Promise<DataWrapperWithTotal<T>>;
