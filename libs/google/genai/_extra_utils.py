# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Extra utils depending on types that are shared between sync and async modules."""

import inspect
import logging
import sys
import typing
from typing import Any, Callable, Dict, Optional, Union, get_args, get_origin

import pydantic

from . import _common
from . import errors
from . import types

if sys.version_info >= (3, 10):
  from types import UnionType
else:
  UnionType = typing._UnionGenericAlias  # type: ignore[attr-defined]

_DEFAULT_MAX_REMOTE_CALLS_AFC = 10

logger = logging.getLogger('google_genai.models')


def _create_generate_content_config_model(
    config: types.GenerateContentConfigOrDict,
) -> types.GenerateContentConfig:
  if isinstance(config, dict):
    return types.GenerateContentConfig(**config)
  else:
    return config


def format_destination(
    src: str,
    config: Optional[types.CreateBatchJobConfigOrDict] = None,
) -> types.CreateBatchJobConfig:
  """Formats the destination uri based on the source uri."""
  config = (
      types._CreateBatchJobParameters(config=config).config
      or types.CreateBatchJobConfig()
  )

  unique_name = None
  if not config.display_name:
    unique_name = _common.timestamped_unique_name()
    config.display_name = f'genai_batch_job_{unique_name}'

  if not config.dest:
    if src.startswith('gs://') and src.endswith('.jsonl'):
      # If source uri is "gs://bucket/path/to/src.jsonl", then the destination
      # uri prefix will be "gs://bucket/path/to/src/dest".
      config.dest = f'{src[:-6]}/dest'
    elif src.startswith('bq://'):
      # If source uri is "bq://project.dataset.src", then the destination
      # uri will be "bq://project.dataset.src_dest_TIMESTAMP_UUID".
      unique_name = unique_name or _common.timestamped_unique_name()
      config.dest = f'{src}_dest_{unique_name}'
    else:
      raise ValueError(f'Unsupported source: {src}')
  return config


def get_function_map(
    config: Optional[types.GenerateContentConfigOrDict] = None,
    is_caller_method_async: bool = False,
) -> dict[str, Callable[..., Any]]:
  """Returns a function map from the config."""
  function_map: dict[str, Callable[..., Any]] = {}
  if not config:
    return function_map
  config_model = _create_generate_content_config_model(config)
  if config_model.tools:
    for tool in config_model.tools:
      if callable(tool):
        if inspect.iscoroutinefunction(tool) and not is_caller_method_async:
          raise errors.UnsupportedFunctionError(
              f'Function {tool.__name__} is a coroutine function, which is not'
              ' supported for automatic function calling. Please manually'
              f' invoke {tool.__name__} to get the function response.'
          )
        function_map[tool.__name__] = tool
  return function_map


def convert_number_values_for_dict_function_call_args(
    args: dict[str, Any],
) -> dict[str, Any]:
  """Converts float values in dict with no decimal to integers."""
  return {
      key: convert_number_values_for_function_call_args(value)
      for key, value in args.items()
  }


def convert_number_values_for_function_call_args(
    args: Union[dict[str, object], list[object], object],
) -> Union[dict[str, object], list[object], object]:
  """Converts float values with no decimal to integers."""
  if isinstance(args, float) and args.is_integer():
    return int(args)
  if isinstance(args, dict):
    return {
        key: convert_number_values_for_function_call_args(value)
        for key, value in args.items()
    }
  if isinstance(args, list):
    return [
        convert_number_values_for_function_call_args(value) for value in args
    ]
  return args


def is_annotation_pydantic_model(annotation: Any) -> bool:
  try:
    return inspect.isclass(annotation) and issubclass(
        annotation, pydantic.BaseModel
    )
  # for python 3.10 and below, inspect.isclass(annotation) has inconsistent
  # results with versions above. for example, inspect.isclass(dict[str, int]) is
  # True in 3.10 and below but False in 3.11 and above.
  except TypeError:
    return False


def convert_if_exist_pydantic_model(
    value: Any, annotation: Any, param_name: str, func_name: str
) -> Any:
  if isinstance(value, dict) and is_annotation_pydantic_model(annotation):
    try:
      return annotation(**value)
    except pydantic.ValidationError as e:
      raise errors.UnknownFunctionCallArgumentError(
          f'Failed to parse parameter {param_name} for function'
          f' {func_name} from function call part because function call argument'
          f' value {value} is not compatible with parameter annotation'
          f' {annotation}, due to error {e}'
      )
  if isinstance(value, list) and get_origin(annotation) == list:
    item_type = get_args(annotation)[0]
    return [
        convert_if_exist_pydantic_model(item, item_type, param_name, func_name)
        for item in value
    ]
  if isinstance(value, dict) and get_origin(annotation) == dict:
    _, value_type = get_args(annotation)
    return {
        k: convert_if_exist_pydantic_model(v, value_type, param_name, func_name)
        for k, v in value.items()
    }
  # example 1: typing.Union[int, float]
  # example 2: int | float equivalent to UnionType[int, float]
  if get_origin(annotation) in (Union, UnionType):
    for arg in get_args(annotation):
      if (
          (get_args(arg) and get_origin(arg) is list)
          or isinstance(value, arg)
          or (isinstance(value, dict) and is_annotation_pydantic_model(arg))
      ):
        try:
          return convert_if_exist_pydantic_model(
              value, arg, param_name, func_name
          )
        # do not raise here because there could be multiple pydantic model types
        # in the union type.
        except pydantic.ValidationError:
          continue
    # if none of the union type is matched, raise error
    raise errors.UnknownFunctionCallArgumentError(
        f'Failed to parse parameter {param_name} for function'
        f' {func_name} from function call part because function call argument'
        f' value {value} cannot be converted to parameter annotation'
        f' {annotation}.'
    )
  # the only exception for value and annotation type to be different is int and
  # float. see convert_number_values_for_function_call_args function for context
  if isinstance(value, int) and annotation is float:
    return value
  if not isinstance(value, annotation):
    raise errors.UnknownFunctionCallArgumentError(
        f'Failed to parse parameter {param_name} for function {func_name} from'
        f' function call part because function call argument value {value} is'
        f' not compatible with parameter annotation {annotation}.'
    )
  return value


def convert_argument_from_function(
    args: dict[str, Any], function: Callable[..., Any]
) -> dict[str, Any]:
  signature = inspect.signature(function)
  func_name = function.__name__
  converted_args = {}
  for param_name, param in signature.parameters.items():
    if param_name in args:
      converted_args[param_name] = convert_if_exist_pydantic_model(
          args[param_name],
          param.annotation,
          param_name,
          func_name,
      )
  return converted_args


def invoke_function_from_dict_args(
    args: Dict[str, Any], function_to_invoke: Callable[..., Any]
) -> Any:
  converted_args = convert_argument_from_function(args, function_to_invoke)
  try:
    return function_to_invoke(**converted_args)
  except Exception as e:
    raise errors.FunctionInvocationError(
        f'Failed to invoke function {function_to_invoke.__name__} with'
        f' converted arguments {converted_args} from model returned function'
        f' call argument {args} because of error {e}'
    )


async def invoke_function_from_dict_args_async(
    args: Dict[str, Any], function_to_invoke: Callable[..., Any]
) -> Any:
  converted_args = convert_argument_from_function(args, function_to_invoke)
  try:
    return await function_to_invoke(**converted_args)
  except Exception as e:
    raise errors.FunctionInvocationError(
        f'Failed to invoke function {function_to_invoke.__name__} with'
        f' converted arguments {converted_args} from model returned function'
        f' call argument {args} because of error {e}'
    )


def get_function_response_parts(
    response: types.GenerateContentResponse,
    function_map: dict[str, Callable[..., Any]],
) -> list[types.Part]:
  """Returns the function response parts from the response."""
  func_response_parts = []
  if (
      response.candidates is not None
      and isinstance(response.candidates[0].content, types.Content)
      and response.candidates[0].content.parts is not None
  ):
    for part in response.candidates[0].content.parts:
      if not part.function_call:
        continue
      func_name = part.function_call.name
      if func_name is not None and part.function_call.args is not None:
        func = function_map[func_name]
        args = convert_number_values_for_dict_function_call_args(
            part.function_call.args
        )
        func_response: dict[str, Any]
        try:
          func_response = {
              'result': invoke_function_from_dict_args(args, func)
          }
        except Exception as e:  # pylint: disable=broad-except
          func_response = {'error': str(e)}
        func_response_part = types.Part.from_function_response(
            name=func_name, response=func_response
        )
        func_response_parts.append(func_response_part)
  return func_response_parts

async def get_function_response_parts_async(
    response: types.GenerateContentResponse,
    function_map: dict[str, Callable[..., Any]],
) -> list[types.Part]:
  """Returns the function response parts from the response."""
  func_response_parts = []
  if (
      response.candidates is not None
      and isinstance(response.candidates[0].content, types.Content)
      and response.candidates[0].content.parts is not None
  ):
    for part in response.candidates[0].content.parts:
      if not part.function_call:
        continue
      func_name = part.function_call.name
      if func_name is not None and part.function_call.args is not None:
        func = function_map[func_name]
        args = convert_number_values_for_dict_function_call_args(
            part.function_call.args
        )
        func_response: dict[str, Any]
        try:
          if inspect.iscoroutinefunction(func):
            func_response = {
                'result': await invoke_function_from_dict_args_async(args, func)
            }
          else:
            func_response = {
                'result': invoke_function_from_dict_args(args, func)
            }
        except Exception as e:  # pylint: disable=broad-except
          func_response = {'error': str(e)}
        func_response_part = types.Part.from_function_response(
            name=func_name, response=func_response
        )
        func_response_parts.append(func_response_part)
  return func_response_parts


def should_disable_afc(
    config: Optional[types.GenerateContentConfigOrDict] = None,
) -> bool:
  """Returns whether automatic function calling is enabled."""
  if not config:
    return False
  config_model = _create_generate_content_config_model(config)
  # If max_remote_calls is less or equal to 0, warn and disable AFC.
  if (
      config_model
      and config_model.automatic_function_calling
      and config_model.automatic_function_calling.maximum_remote_calls
      is not None
      and int(config_model.automatic_function_calling.maximum_remote_calls) <= 0
  ):
    logger.warning(
        'max_remote_calls in automatic_function_calling_config'
        f' {config_model.automatic_function_calling.maximum_remote_calls} is'
        ' less than or equal to 0. Disabling automatic function calling.'
        ' Please set max_remote_calls to a positive integer.'
    )
    return True

  # Default to enable AFC if not specified.
  if (
      not config_model.automatic_function_calling
      or config_model.automatic_function_calling.disable is None
  ):
    return False

  if (
      config_model.automatic_function_calling.disable
      and config_model.automatic_function_calling.maximum_remote_calls
      is not None
      # exclude the case where max_remote_calls is set to 10 by default.
      and 'maximum_remote_calls'
      in config_model.automatic_function_calling.model_fields_set
      and int(config_model.automatic_function_calling.maximum_remote_calls) > 0
  ):
    logger.warning(
        '`automatic_function_calling.disable` is set to `True`. And'
        ' `automatic_function_calling.maximum_remote_calls` is a'
        ' positive number'
        f' {config_model.automatic_function_calling.maximum_remote_calls}.'
        ' Disabling automatic function calling. If you want to enable'
        ' automatic function calling, please set'
        ' `automatic_function_calling.disable` to `False` or leave it unset,'
        ' and set `automatic_function_calling.maximum_remote_calls` to a'
        ' positive integer or leave'
        ' `automatic_function_calling.maximum_remote_calls` unset.'
    )

  return config_model.automatic_function_calling.disable


def get_max_remote_calls_afc(
    config: Optional[types.GenerateContentConfigOrDict] = None,
) -> int:
  if not config:
    return _DEFAULT_MAX_REMOTE_CALLS_AFC
  """Returns the remaining remote calls for automatic function calling."""
  if should_disable_afc(config):
    raise ValueError(
        'automatic function calling is not enabled, but SDK is trying to get'
        ' max remote calls.'
    )
  config_model = _create_generate_content_config_model(config)
  if (
      not config_model.automatic_function_calling
      or config_model.automatic_function_calling.maximum_remote_calls is None
  ):
    return _DEFAULT_MAX_REMOTE_CALLS_AFC
  return int(config_model.automatic_function_calling.maximum_remote_calls)


def should_append_afc_history(
    config: Optional[types.GenerateContentConfigOrDict] = None,
) -> bool:
  if not config:
    return True
  config_model = _create_generate_content_config_model(config)
  if not config_model.automatic_function_calling:
    return True
  return not config_model.automatic_function_calling.ignore_call_history
