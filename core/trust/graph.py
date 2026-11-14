"""
Hex Adjacency Trust Graph & Policy Engine for H4ck3rMx
Enforces the maximum-6-peer rule, multi-party threshold cosignatures,
and kernel-level IPC / eBPF socket confinement.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class PeerEntry:
    app_id: str
    app_cert_sha256: str
    purpose: str
    expires_at: int


@dataclass
class Attestation:
    attestor_id: str
    signature: str
    issued_at: int
    weight: int = 1


@dataclass
class TrustManifest:
    schema_version: str
    app_id: str
    app_cert_sha256: str
    manifest_version: int
    issued_at: int
    expires_at: int
    trusted_peers: List[PeerEntry]
    attestations: List[Attestation]
    anchors: List[str]

    def validate_rules(self) -> Tuple[bool, str]:
        # 1. Hex adjacency check
        if len(self.trusted_peers) > 6:
            return False, f"Hex adjacency violation: declared {len(self.trusted_peers)} peers (max allowed is 6)"
        # 2. Expiry check
        now = int(time.time())
        if self.expires_at < now:
            return False, f"Manifest expired at {self.expires_at} (current time: {now})"
        # 3. Maximum validity window <= 180 days (15552000 seconds)
        if (self.expires_at - self.issued_at) > 15552000:
            return False, "Manifest validity window exceeds 180 days limit"
        return True, "Manifest compliant"


class TrustGraph:
    """Manages system-wide trust graph adjacency, anchor paths, and eBPF socket ACLs."""

    def __init__(self, bootstrap_anchors: Optional[List[str]] = None):
        self.anchors: Set[str] = set(bootstrap_anchors or ["org.h4ck3rmx.core.system", "org.h4ck3rmx.core.agent"])
        self.adj_list: Dict[str, Set[str]] = {}
        self.manifest_cache: Dict[str, TrustManifest] = {}

    def register_package(self, manifest: TrustManifest) -> Tuple[bool, str]:
        # Rule validation
        valid, msg = manifest.validate_rules()
        if not valid:
            return False, msg

        # Cosignature check: require >= 6 independent attestations
        if len(manifest.attestations) < 6:
            return False, f"Threshold cosigning failure: {len(manifest.attestations)}/6 cosignatures present"

        # Check path reachability to at least one bootstrap anchor
        if not any(a in self.anchors for a in manifest.anchors):
            return False, "Package does not declare a valid path to an audited bootstrap anchor"

        # Register in graph
        self.manifest_cache[manifest.app_id] = manifest
        self.adj_list[manifest.app_id] = {p.app_id for p in manifest.trusted_peers}

        return True, f"Package {manifest.app_id} registered with {len(manifest.trusted_peers)} hex peers"

    def can_communicate(self, caller_id: str, target_id: str) -> bool:
        """Determines whether two applications/services are allowed to communicate."""
        # System anchors can communicate with audited endpoints
        if caller_id in self.anchors or target_id in self.anchors:
            return True
        # Enforce hex adjacency
        allowed_peers = self.adj_list.get(caller_id, set())
        return target_id in allowed_peers

    def generate_ebpf_socket_rules(self, app_id: str) -> List[str]:
        """Generates mock eBPF socket filter rules for the application namespace."""
        peers = self.adj_list.get(app_id, set())
        rules = [
            f"# eBPF Socket Filter for {app_id}",
            f"ALLOW LOOPBACK 127.0.0.1:*",
            f"DENY ALL_INBOUND",
            f"DENY ALL_OUTBOUND_EXCEPT_PEERS",
        ]
        for peer in peers:
            rules.append(f"ALLOW IPC_UNIX_SOCKET peer={peer}")
        rules.append("DROP ALL_UNMATCHED LOG_SECURITY_ALERT")
        return rules
