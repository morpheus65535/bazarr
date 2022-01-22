export const actionOptions: SelectorOption<History.ActionOptions>[] = [
  {
    label: "Automatically Downloaded",
    value: 1,
  },
  {
    label: "Manually Downloaded",
    value: 2,
  },
  {
    label: "Upgraded",
    value: 3,
  },
];

export const timeFrameOptions: SelectorOption<History.TimeFrameOptions>[] = [
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
