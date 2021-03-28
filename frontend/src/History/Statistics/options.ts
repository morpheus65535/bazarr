export const actionOptions: SelectorOption<History.ActionOptions>[] = [
  {
    label: "Automatically Downloaded",
    value: 0,
  },
  {
    label: "Manually Downloaded",
    value: 1,
  },
  {
    label: "Upgraded",
    value: 2,
  },
];

export const timeframeOptions: SelectorOption<History.TimeframeOptions>[] = [
  {
    label: "Last Week",
    value: "week",
  },
  {
    label: "Last Month",
    value: "month",
  },
  {
    label: "Last Trimester",
    value: "trimester",
  },
  {
    label: "Last Year",
    value: "year",
  },
];
