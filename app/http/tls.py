"""Finding, describing and (for local work) making a TLS certificate.

Nothing here talks to a certificate authority.  Getting a real certificate is
certbot's job and it does it well; this module's job is to find what certbot
left behind, to say clearly what is missing when it has not run yet, and to
produce a throwaway self-signed pair so ``--https`` works on a laptop with no
domain at all.

The search order is deliberate: an explicit ``--cert``/``--key`` wins, because
somebody who passes a path means it; then Let's Encrypt's own layout, because
that is where certbot puts things and it is where a renewal will put the new
one too; then a self-signed pair we made earlier, which is only ever used
after ``--self-signed`` asked for it.
"""
from __future__ import annotations

import os
import shutil
import ssl
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from .. import config

LETSENCRYPT = Path("/etc/letsencrypt/live")
SELF_SIGNED_DIR = config.DATA_DIR / "tls"
# Browsers refuse a self-signed certificate valid for longer than this, and
# there is no reason for a development one to outlive it.
SELF_SIGNED_DAYS = 820


class TLSError(Exception):
    pass


def letsencrypt_paths(domain: str) -> Tuple[str, str]:
    live = LETSENCRYPT / domain
    return str(live / "fullchain.pem"), str(live / "privkey.pem")


def self_signed_paths(domain: str) -> Tuple[str, str]:
    name = domain or "localhost"
    return (str(SELF_SIGNED_DIR / ("%s.crt" % name)),
            str(SELF_SIGNED_DIR / ("%s.key" % name)))


def _readable(*paths: str) -> bool:
    return all(p and os.path.isfile(p) and os.access(p, os.R_OK) for p in paths)


def locate(domain: str = "", cert: str = "", key: str = "",
           allow_self_signed: bool = False) -> Optional[Dict[str, str]]:
    """The certificate to serve with, or None if there is not one yet.

    Returns ``{"cert", "key", "source"}``.  ``source`` is for the operator:
    it is the difference between "this is the real certificate for your
    domain" and "this is the throwaway one, every browser will warn".
    """
    if cert or key:
        if not _readable(cert, key):
            raise TLSError("--cert/--key given but not both readable: %s, %s"
                           % (cert or "(none)", key or "(none)"))
        return {"cert": cert, "key": key, "source": "given on the command line"}
    if domain:
        le_cert, le_key = letsencrypt_paths(domain)
        if _readable(le_cert, le_key):
            return {"cert": le_cert, "key": le_key,
                    "source": "Let's Encrypt (%s)" % (LETSENCRYPT / domain)}
    if allow_self_signed:
        ss_cert, ss_key = self_signed_paths(domain)
        if not _readable(ss_cert, ss_key):
            make_self_signed(domain)
        return {"cert": ss_cert, "key": ss_key, "source": "self-signed"}
    return None


def make_self_signed(domain: str = "") -> Tuple[str, str]:
    """Write a self-signed certificate for local work.

    Python's ssl module can use a certificate but cannot mint one, and this
    project ships without dependencies, so this shells out to openssl -- which
    is on anything that can already serve TLS.  The certificate covers the
    domain if there is one plus localhost and 127.0.0.1, because the machine
    running it is usually reached by all three.
    """
    openssl = shutil.which("openssl")
    if not openssl:
        raise TLSError(
            "openssl is not on PATH, so a self-signed certificate cannot be "
            "made here.  Pass a real one with --cert/--key, or install "
            "openssl.")
    SELF_SIGNED_DIR.mkdir(parents=True, exist_ok=True)
    cert, key = self_signed_paths(domain)
    names = ["DNS:localhost", "IP:127.0.0.1"]
    if domain:
        names.insert(0, "DNS:%s" % domain)
    cmd = [openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
           "-keyout", key, "-out", cert,
           "-days", str(SELF_SIGNED_DAYS),
           "-subj", "/CN=%s" % (domain or "localhost"),
           "-addext", "subjectAltName=%s" % ",".join(names)]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise TLSError("openssl could not write a certificate: %s"
                       % result.stderr.decode("utf-8", "replace").strip())
    os.chmod(key, 0o600)
    return cert, key


def describe(cert: str) -> Dict[str, str]:
    """What is in the certificate, for the start-up banner.

    Read with the ssl module's own decoder.  If it is not available -- it is
    not a documented API -- the server still starts; only the banner is
    poorer for it.
    """
    out: Dict[str, str] = {}
    try:
        import ssl as _ssl
        raw = _ssl._ssl._test_decode_cert(cert)  # type: ignore[attr-defined]
    except Exception:
        return out
    try:
        for part in raw.get("subject", ()):
            for k, v in part:
                if k == "commonName":
                    out["name"] = v
        names = [v for k, v in raw.get("subjectAltName", ()) if k == "DNS"]
        if names:
            out["names"] = ", ".join(names)
        not_after = raw.get("notAfter")
        if not_after:
            left = ssl.cert_time_to_seconds(not_after) - time.time()
            out["expires"] = not_after
            out["days_left"] = str(int(left // 86400))
    except Exception:
        pass
    return out


def certbot_hint(domain: str, webroot: Optional[Path] = None) -> str:
    """The exact command that turns a working port 80 into a certificate."""
    root = webroot or config.ACME_WEBROOT
    name = domain or "your-domain.example"
    return (
        "  sudo certbot certonly --webroot -w %s -d %s\n"
        "then restart with --domain %s.  Leave the server running while\n"
        "certbot works: it answers the challenge on port 80 itself."
        % (root, name, name))
