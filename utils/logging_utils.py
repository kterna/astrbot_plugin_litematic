"""
日志工具模块，提供统一的日志记录功能
"""
import logging
import traceback
from typing import Dict, Any, Optional, Type, Union
from astrbot import logger

from .exceptions import LitematicPluginError


def log_error(error: Union[LitematicPluginError, Exception], 
              level: int = logging.ERROR, 
              extra_info: Optional[Dict[str, Any]] = None) -> None:
    """统一记录错误日志
    
    Args:
        error: 错误对象
        level: 日志级别
        extra_info: 额外信息
    """
    # 准备日志信息
    log_info = {}
    
    # 添加额外信息
    if extra_info:
        # 防止与LogRecord的预留属性冲突
        if 'filename' in extra_info:
            extra_copy = extra_info.copy()
            extra_copy['file_name'] = extra_copy.pop('filename')
            log_info.update(extra_copy)
        else:
            log_info.update(extra_info)
    
    # 如果是插件自定义异常，记录详细信息
    if isinstance(error, LitematicPluginError):
        error_code = getattr(error, 'code', 0)
        error_details = getattr(error, 'details', {})
        error_message = str(error)
        
        # 防止与LogRecord的预留属性冲突
        if 'filename' in error_details:
            error_details = error_details.copy()
            error_details['file_name'] = error_details.pop('filename')
        
        log_info.update({
            'error_code': error_code,
            'error_details': error_details
        })
        
        log_message = f"[错误 {error_code}] {error_message}"
    else:
        # 通用异常
        error_type = type(error).__name__
        error_message = str(error)
        log_message = f"[{error_type}] {error_message}"
        
        # 添加堆栈信息
        if level >= logging.ERROR:
            log_info['traceback'] = traceback.format_exc()
    
    # 根据日志级别记录
    if level >= logging.ERROR:
        logger.error(log_message, extra=log_info)
    elif level >= logging.WARNING:
        logger.warning(log_message, extra=log_info)
    elif level >= logging.INFO:
        logger.info(log_message, extra=log_info)
    else:
        logger.debug(log_message, extra=log_info)


def log_exception(exc_type: Type[Exception], exc_value: Exception, 
                  exc_traceback: traceback, 
                  extra_info: Optional[Dict[str, Any]] = None) -> None:
    """记录未捕获的异常
    
    Args:
        exc_type: 异常类型
        exc_value: 异常值
        exc_traceback: 异常堆栈
        extra_info: 额外信息
    """
    log_info = {
        'exc_type': exc_type.__name__,
        'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    }
    
    if extra_info:
        log_info.update(extra_info)
    
    logger.error(f"未捕获的异常: {exc_value}", extra=log_info)


def log_operation(operation: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
    """记录操作日志
    
    Args:
        operation: 操作名称
        success: 是否成功
        details: 操作详情
    """
    log_info = {}
    if details:
        # 防止与LogRecord的预留属性冲突
        if 'filename' in details:
            details_copy = details.copy()
            details_copy['file_name'] = details_copy.pop('filename')
            log_info.update(details_copy)
        else:
            log_info.update(details)
    
    level = logging.INFO if success else logging.WARNING
    status = "成功" if success else "失败"
    
    log_message = f"操作 '{operation}' {status}"
    
    if level >= logging.ERROR:
        logger.error(log_message, extra=log_info)
    elif level >= logging.WARNING:
        logger.warning(log_message, extra=log_info)
    else:
        logger.info(log_message, extra=log_info) 