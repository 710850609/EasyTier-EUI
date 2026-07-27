#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Data models matching FFI NetworkInstanceRunningInfo structure"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Ipv4Addr:
    addr: int = 0


@dataclass
class Ipv4Inet:
    address: Optional[Ipv4Addr] = None
    network_length: int = 0

    @classmethod
    def from_dict(cls, d: Optional[Dict]) -> Optional['Ipv4Inet']:
        if not d:
            return None
        return cls(
            address=Ipv4Addr(**(d.get('address') or {})) if d.get('address') else None,
            network_length=d.get('network_length', 0),
        )


@dataclass
class Ipv6Addr:
    part1: int = 0
    part2: int = 0
    part3: int = 0
    part4: int = 0


@dataclass
class Url:
    url: str = ""


@dataclass
class StunInfo:
    udp_nat_type: int = 0
    tcp_nat_type: int = 0
    last_update_time: int = 0


@dataclass
class NodeInfo:
    virtual_ipv4: Optional[Ipv4Inet] = None
    hostname: str = ""
    version: str = ""
    ips: Optional[Dict] = None
    stun_info: Optional[StunInfo] = None
    listeners: List[Url] = field(default_factory=list)
    vpn_portal_cfg: Optional[str] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict]) -> Optional['NodeInfo']:
        if not d:
            return None
        return cls(
            virtual_ipv4=Ipv4Inet.from_dict(d.get('virtual_ipv4')),
            hostname=d.get('hostname', ''),
            version=d.get('version', ''),
            ips=d.get('ips'),
            stun_info=StunInfo(**(d.get('stun_info') or {})) if d.get('stun_info') else None,
            listeners=[Url(**(u or {})) for u in (d.get('listeners') or [])],
            vpn_portal_cfg=d.get('vpn_portal_cfg'),
        )


@dataclass
class TunnelInfo:
    tunnel_type: str = ""
    local_addr: Optional[Url] = None
    remote_addr: Optional[Url] = None


@dataclass
class PeerConnStats:
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_packets: int = 0
    tx_packets: int = 0
    latency_us: int = 0


@dataclass
class PeerConnInfo:
    conn_id: str = ""
    my_peer_id: int = 0
    is_client: bool = False
    peer_id: int = 0
    features: List[str] = field(default_factory=list)
    tunnel: Optional[TunnelInfo] = None
    stats: Optional[PeerConnStats] = None
    loss_rate: float = 0.0


@dataclass
class PeerInfo:
    peer_id: int = 0
    conns: List[PeerConnInfo] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: Optional[Dict]) -> Optional['PeerInfo']:
        if not d:
            return None
        return cls(
            peer_id=d.get('peer_id', 0),
            conns=[PeerConnInfo(**(c or {})) for c in (d.get('conns') or [])],
        )


@dataclass
class Route:
    peer_id: int = 0
    ipv4_addr: Optional[Any] = None
    next_hop_peer_id: int = 0
    cost: int = 0
    proxy_cidrs: List[str] = field(default_factory=list)
    hostname: str = ""
    stun_info: Optional[StunInfo] = None
    inst_id: str = ""
    version: str = ""


@dataclass
class PeerRoutePair:
    route: Optional[Route] = None
    peer: Optional[PeerInfo] = None


@dataclass
class RouteForeignNetworkSummary:
    hostname: str = ""
    virtual_ipv4: Optional[Ipv4Inet] = None
    cost: int = 0


@dataclass
class NetworkInstanceInfo:
    """Matches FFI NetworkInstanceRunningInfo protobuf structure"""
    dev_name: str = ""
    my_node_info: Optional[NodeInfo] = None
    events: List[str] = field(default_factory=list)
    routes: List[Route] = field(default_factory=list)
    peers: List[PeerInfo] = field(default_factory=list)
    peer_route_pairs: List[PeerRoutePair] = field(default_factory=list)
    running: bool = False
    error_msg: Optional[str] = None
    foreign_network_summary: Optional[RouteForeignNetworkSummary] = None

    @classmethod
    def from_dict(cls, d: Optional[Dict]) -> 'NetworkInstanceInfo':
        if not d:
            return cls()
        return cls(
            dev_name=d.get('dev_name', ''),
            my_node_info=NodeInfo.from_dict(d.get('my_node_info')),
            events=d.get('events') or [],
            routes=[Route(**(r or {})) for r in (d.get('routes') or [])],
            peers=[PeerInfo.from_dict(p) for p in (d.get('peers') or []) if p],
            peer_route_pairs=[
                PeerRoutePair(
                    route=Route(**(p.get('route') or {})) if p.get('route') else None,
                    peer=PeerInfo.from_dict(p.get('peer')) if p.get('peer') else None,
                )
                for p in (d.get('peer_route_pairs') or [])
            ],
            running=d.get('running', False),
            error_msg=d.get('error_msg'),
            foreign_network_summary=RouteForeignNetworkSummary(
                **(d.get('foreign_network_summary') or {})
            ) if d.get('foreign_network_summary') else None,
        )

    def to_json_serializable(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict for API responses"""
        from dataclasses import asdict
        return asdict(self)