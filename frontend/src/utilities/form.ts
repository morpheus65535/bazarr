const validation =
  <T>(condition: (value: T) => boolean, message: string) =>
  (value: T) => {
    if (condition(value)) {
      return null;
    } else {
      return message;
    }
  };

const FormUtils = {
  validation,
};

export default FormUtils;
