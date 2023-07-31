#!/usr/bin/env python3.5


class BaseIndicator:
    def __init__(self, args):
        self.args = args

    def calculate(self, **data):
        raise NotImplementedError()

    def decide_signal(self, **data):
        raise NotImplementedError()