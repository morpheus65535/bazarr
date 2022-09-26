function validation<T>(condition: (value: T) => boolean, message: string) {
  return (value: T) => {
    if (condition(value)) {
      return null;
    } else {
      return message;
    }
  };
}

const FormUtils = {
  validation,
};

export default FormUtils;
