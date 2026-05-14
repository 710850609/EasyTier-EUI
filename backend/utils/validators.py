from pathlib import Path
from typing import Optional, Any, Tuple

from http_dispatcher.dispatcher import HttpException
from utils import security, run_configs


class Validator:

    @staticmethod
    def not_empty(params: Optional[dict], key: Optional[str], message: Optional[str]=None, raise_error: bool=True) -> Tuple[Any, bool]:
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
            raise HttpException(message if message else f"{key} is Empty")
        return value, result


    @staticmethod
    def check_profile(profile:Optional[str], check_exists:bool = True) -> Optional[str]:
        """检查配置文件名"""
        if not profile:
            raise HttpException("未知profile")
        profile = security.validate_profile(profile)
        if check_exists and (profile is None or not Path(run_configs.et_config_file(profile)).exists()):
            raise HttpException(f"配置文件不存在: {profile}")
        return profile