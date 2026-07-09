#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timezone, timedelta

_TIMESTAMP_FMT = '%Y%m%d_%H%M%S'
_DISPLAY_TZ = timezone(timedelta(hours=9))  # KST (UTC+9)


def current_timestamp_utc() -> str:
    """Return current time as UTC wall-clock string for internal storage."""
    return datetime.now(timezone.utc).strftime(_TIMESTAMP_FMT)


def timestamp_for_filename(utc_timestamp: str) -> str:
    """Convert UTC storage timestamp to KST for file and directory names."""
    if not utc_timestamp:
        return current_timestamp_for_filename()
    return _parse_utc_timestamp(utc_timestamp).astimezone(_DISPLAY_TZ).strftime(_TIMESTAMP_FMT)


def current_timestamp_for_filename() -> str:
    """Return current time as KST wall-clock string for file and directory names."""
    return timestamp_for_filename(current_timestamp_utc())


def _parse_utc_timestamp(value: str) -> datetime:
    return datetime.strptime(value, _TIMESTAMP_FMT).replace(tzinfo=timezone.utc)


def format_display_time(value: str) -> str:
    return _parse_utc_timestamp(value).astimezone(_DISPLAY_TZ).strftime('%Y%m%d_%H:%M:%S')


def _format_duration_compact(total_seconds: int) -> str:
    total_seconds = max(0, total_seconds)
    hours, remaining_seconds = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remaining_seconds, 60)

    duration_items = []
    if hours > 0:
        duration_items.append(f'{hours}h')
    if minutes > 0:
        duration_items.append(f'{minutes}m')
    duration_items.append(f'{seconds}s')
    return f'({" ".join(duration_items)})'


def format_running_time(start_time: str, finish_time: str) -> str:
    start_utc = _parse_utc_timestamp(start_time)
    finish_utc = _parse_utc_timestamp(finish_time)
    total_seconds = int((finish_utc - start_utc).total_seconds())

    start_display = start_utc.astimezone(_DISPLAY_TZ).strftime('%Y%m%d_%H:%M:%S')
    finish_display = finish_utc.astimezone(_DISPLAY_TZ).strftime('%Y%m%d_%H:%M:%S')
    duration = _format_duration_compact(total_seconds)

    return f'{start_display} ~ {finish_display} {duration}'
