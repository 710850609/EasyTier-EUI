from pathlib import Path
from typing import Optional, Any, Tuple

from http_dispatcher.dispatcher import HttpException
from locales import get_message
from utils import security, run_configs


class Validator:

    @staticmethod
    def not_empty(params: Optional[dict], key: Optional[str], message_key: Optional[str]=None, raise_error: bool=True, **kwargs) -> Tuple[Any, bool]:
        if key is None:
            raise AssertionError(f"not key for check")
        value = None
        if not params:
            result = False
        else:
            value = params.get(key)
            if value is None:
                result = False
            elif isinstance(value, str) and len(value.strip()) == 0:
                result = False
            elif isinstance(value, list) and len(value) == 0:
                result = False
            elif isinstance(value, dict) and len(value.items()) == 0:
                result = False
            else:
                result = True
        if raise_error and not result:
            if message_key:
                raise HttpException(get_message(message_key, **kwargs))
            else:
                raise HttpException(f"{key} is Empty")
        return value, result


    @staticmethod
    def check_profile(profile:Optional[str], check_exists:bool = True) -> str:
        """检查配置文件名"""
        if not profile:
            raise HttpException(get_message('validate.unknown_profile'))
        profile = security.validate_profile(profile)
        if check_exists and (profile is None or not Path(run_configs.et_config_file(profile)).exists()):
            raise HttpException(get_message('validate.config_not_found', profile=profile))
        return profile