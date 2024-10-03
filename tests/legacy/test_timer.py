#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2021 LG Electronics Inc.
# SPDX-License-Identifier: Apache-2.0
import time
from fosslight_util.timer_thread import TimerThread


def main():
    timer = TimerThread()
    timer.setDaemon(True)
    timer.start()

    time.sleep(3)


if __name__ == '__main__':
    main()
