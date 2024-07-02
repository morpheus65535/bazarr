interface TimeFormat {
  unit: string;
  divisor: number;
}

export const divisorDay = 24 * 60 * 60;
export const divisorHour = 60 * 60;
export const divisorMinute = 60;
export const divisorSecond = 1;

export const formatTime = (
  timeInSeconds: number,
  formats: TimeFormat[],
): string => {
  return formats.reduce(
    (
      { formattedTime, remainingSeconds },
      { unit, divisor }: TimeFormat,
      index: number,
    ) => {
      const timeValue = Math.floor(remainingSeconds / divisor);

      const seconds = remainingSeconds % divisor;

      const time =
        formattedTime +
        (index === 0
          ? `${timeValue}${unit} `
          : `${timeValue.toString().padStart(2, "0")}${index < formats.length - 1 ? ":" : ""}`);

      return {
        formattedTime: time,
        remainingSeconds: seconds,
      };
    },
    { formattedTime: "", remainingSeconds: timeInSeconds },
  ).formattedTime;
};
