export function createMovieId(id: number) {
  return `movie/${id}`;
}

export function createSeriesId(id: number) {
  return `series/${id}`;
}

export function createEpisodeId(id: number) {
  return `episode/${id}`;
}

export function createRangeId(type: string, range: Parameter.Range) {
  const { start, length } = range;
  return `${type}/${start}/${length}`;
}
