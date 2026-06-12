#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class PeersCheckResult(object):
    def __init__(self, uri: str, src_uri: str, relay: int=-1, latency: int=-1, status: int=-1, owner='', **kwargs: dict):
        self.uri = uri
        self.src_uri = src_uri
        self.relay = relay
        self.latency = latency
        self.status = status
        self.owner = owner
        self.dynamic = kwargs.get('dynamic')
        self.hostname = kwargs.get('hostname')
        pass