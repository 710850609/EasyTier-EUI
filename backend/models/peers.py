#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class PeersCheckResult(object):
    def __init__(self, uri: str, resolved_uri: str, relay: int=-1, latency: int=-1, status: int=-1):
        self.uri = uri
        self.resolved_uri = resolved_uri
        self.relay = relay
        self.latency = latency
        self.status = status
        pass