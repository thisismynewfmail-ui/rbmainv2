"""Finding, checking and (for local work) making a TLS certificate.

Nothing here talks to a certificate authority.  Getting a real certificate is
certbot's job -- or your registrar's, or your host's -- and this module's job
is to find what any of them left behind, to say clearly what is wrong when the
browser is going to complain, and to produce a throwaway self-signed pair so
``--self-signed`` works on a laptop with no domain at all.

Three shapes of certificate turn up in practice and all three are understood:

* **certbot's own layout** -- ``/etc/letsencrypt/live/<domain>/fullchain.pem``
  plus ``privkey.pem``.
* **a bundle downloaded from a registrar or host** -- a folder (or a zip that
  was unpacked into one) holding ``domain.cert.pem`` and ``private.key.pem``,
  or ``certificate.crt`` and ``private.key``, or any of a dozen other names.
  Drop it in ``certs/`` and it is found; see ``tools/install_cert.py``.
* **explicit paths** -- ``--cert``/``--key``, which always win, because
  somebody who passes a path means it.

A bundle is not just two files with the right names.  The three things that
actually make a browser say "Not secure" are checked before the server
commits to a certificate, because each one is invisible until a visitor hits
it:

* the private key not matching the certificate (the server would refuse to
  start, but with an error about "key values mismatch" rather than about the
  two files being from different orders),
* the intermediates missing or in the wrong order, which every browser on a
  desktop hides -- it fetches them itself -- and every phone shows,
* a certificate that has expired, or that does not cover the name the site is
  reached by.

``locate()`` therefore gathers every candidate it can find, checks each one,
and returns the best; ``report()`` renders the same findings for a human, and
is what ``main.py --tls-check`` prints.
"""
from __future__ import annotations

import os
import shutil
import ssl
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from .. import config

LETSENCRYPT = Path("/etc/letsencrypt/live")
SELF_SIGNED_DIR = config.DATA_DIR / "tls"
# Where a chain we had to re-assemble or re-order is written.  It holds
# certificates only -- never a key -- so it is ordinary world-readable data.
ASSEMBLED_DIR = config.DATA_DIR / "tls" / "assembled"
# Browsers refuse a self-signed certificate valid for longer than this, and
# there is no reason for a development one to outlive it.
SELF_SIGNED_DAYS = 820

# A bundle is a handful of small text files.  Anything bigger is not one, and
# reading it to find out would be the bug.
MAX_PEM_BYTES = 1024 * 1024
MAX_BUNDLE_FILES = 200
# How far below a bundle directory to look, so that unzipping the download
# straight into certs/ -- which usually makes certs/<domain>-ssl-bundle/ --
# works without anybody having to flatten it by hand.
BUNDLE_DEPTH = 3

PEM_CERT_BEGIN = "-----BEGIN CERTIFICATE-----"
PEM_CERT_END = "-----END CERTIFICATE-----"
_PEM_KEY_MARKERS = ("-----BEGIN PRIVATE KEY-----",
                    "-----BEGIN RSA PRIVATE KEY-----",
                    "-----BEGIN EC PRIVATE KEY-----",
                    "-----BEGIN DSA PRIVATE KEY-----",
                    "-----BEGIN ENCRYPTED PRIVATE KEY-----")

# Known file names, best first.  These only order the search: a bundle whose
# files are named something else entirely is still found, by reading them.
_CERT_NAMES = (
    "fullchain.pem", "fullchain.crt", "fullchain.cer",
    "domain.cert.pem",                      # Porkbun and friends
    "certificate.crt", "certificate.pem",
    "cert.pem", "cert.crt", "cert.cer",
    "server.crt", "server.pem", "ssl.crt",
)
_KEY_NAMES = (
    "privkey.pem", "private.key.pem", "private.key", "private.pem",
    "key.pem", "server.key", "domain.key", "ssl.key",
)
_CHAIN_NAMES = (
    "intermediate.cert.pem", "chain.pem", "ca_bundle.crt", "ca-bundle.crt",
    "ca_bundle.pem", "intermediate.crt", "intermediate.pem",
    "bundle.crt", "chain.crt", "ca.crt",
)
# public.key.pem ships in most bundles and is not a private key; reading it as
# one produces a baffling error a long way from the cause.
_NOT_A_KEY = ("public", "pubkey", "csr", "request")


class TLSError(Exception):
    pass


# --------------------------------------------------------------- small utils
def _readable(*paths: str) -> bool:
    return all(p and os.path.isfile(p) and os.access(p, os.R_OK) for p in paths)


def _read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_PEM_BYTES:
            return ""
        return path.read_text("utf-8", "replace")
    except OSError:
        return ""


def split_pem_certs(text: str) -> List[str]:
    """Every ``BEGIN CERTIFICATE`` block in ``text``, in the order found."""
    blocks: List[str] = []
    rest = text
    while True:
        start = rest.find(PEM_CERT_BEGIN)
        if start < 0:
            break
        end = rest.find(PEM_CERT_END, start)
        if end < 0:
            break
        end += len(PEM_CERT_END)
        blocks.append(rest[start:end].strip() + "\n")
        rest = rest[end:]
    return blocks


def _has_private_key(text: str) -> bool:
    return any(marker in text for marker in _PEM_KEY_MARKERS)


def host_matches(pattern: str, host: str) -> bool:
    """RFC 6125 name matching, with the one wildcard label browsers allow.

    ``*.example.com`` covers ``www.example.com`` and not ``example.com`` nor
    ``a.b.example.com`` -- which is why a bundle for a domain normally carries
    both the wildcard and the bare name, and why a certificate that carries
    only the wildcard makes the apex "Not secure".
    """
    pattern = (pattern or "").strip().strip(".").lower()
    host = (host or "").strip().strip(".").lower()
    if not pattern or not host:
        return False
    if pattern == host:
        return True
    if pattern.startswith("*."):
        suffix = pattern[1:]                       # ".example.com"
        if not host.endswith(suffix):
            return False
        label = host[:-len(suffix)]
        return bool(label) and "." not in label
    return False


# ------------------------------------------------------------ certificate IO
def _decode_with_ssl(path: str) -> Optional[dict]:
    """Decode the first certificate in ``path`` with the ssl module.

    ``_test_decode_cert`` is not a documented API.  It is the only way to read
    a certificate without a third-party dependency, so it is tried first and
    every failure falls through to openssl.
    """
    try:
        import ssl as _ssl
        return _ssl._ssl._test_decode_cert(path)  # type: ignore[attr-defined]
    except Exception:
        return None


def _decode_with_openssl(path: str) -> Optional[dict]:
    """The same fields, read out of ``openssl x509`` instead."""
    openssl = shutil.which("openssl")
    if not openssl:
        return None
    try:
        result = subprocess.run(
            [openssl, "x509", "-in", path, "-noout", "-subject", "-issuer",
             "-dates", "-ext", "subjectAltName"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    out: dict = {}
    names: List[Tuple[str, str]] = []
    for line in result.stdout.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if line.startswith("subject="):
            cn = _cn_from_openssl(line[8:])
            if cn:
                out["subject"] = ((("commonName", cn),),)
            out["_subject_text"] = line[8:].strip()
        elif line.startswith("issuer="):
            cn = _cn_from_openssl(line[7:])
            if cn:
                out["issuer"] = ((("commonName", cn),),)
            out["_issuer_text"] = line[7:].strip()
        elif line.startswith("notBefore="):
            out["notBefore"] = line[10:].strip()
        elif line.startswith("notAfter="):
            out["notAfter"] = line[9:].strip()
        elif line.startswith("DNS:") or ", DNS:" in line:
            for part in line.split(","):
                part = part.strip()
                if part.startswith("DNS:"):
                    names.append(("DNS", part[4:].strip()))
                elif part.startswith("IP Address:"):
                    names.append(("IP Address", part[11:].strip()))
    if names:
        out["subjectAltName"] = tuple(names)
    return out or None


def _cn_from_openssl(text: str) -> str:
    for part in text.replace("/", ",").split(","):
        name, _, value = part.partition("=")
        if name.strip().upper() == "CN":
            return value.strip()
    return ""


def _decode(path: str) -> dict:
    return _decode_with_ssl(path) or _decode_with_openssl(path) or {}


def _rdn_cn(raw, key: str) -> str:
    for part in raw.get(key, ()) or ():
        for k, v in part:
            if k == "commonName":
                return v
    return raw.get("_%s_text" % key, "")


def _full_name(raw, key: str) -> str:
    """The whole distinguished name, for telling two issuers apart."""
    text = raw.get("_%s_text" % key, "")
    if text:
        return text
    bits = []
    for part in raw.get(key, ()) or ():
        for k, v in part:
            bits.append("%s=%s" % (k, v))
    return ", ".join(bits)


def inspect(cert_path: str) -> Dict[str, object]:
    """Everything the start-up banner and ``--tls-check`` need to say.

    Returns ``{}`` when the certificate cannot be read at all: the server
    still starts in that case, only the read-out is poorer for it.
    """
    out: Dict[str, object] = {}
    raw = _decode(cert_path)
    if not raw:
        return out
    common = _rdn_cn(raw, "subject")
    if common:
        out["name"] = common
    issuer = _rdn_cn(raw, "issuer")
    if issuer:
        out["issuer"] = issuer
    names = [v for k, v in raw.get("subjectAltName", ()) or () if k == "DNS"]
    if not names and common:
        names = [common]                    # pre-SAN certificate, or openssl
    out["names"] = names
    out["self_signed"] = bool(
        common and issuer
        and _full_name(raw, "subject") == _full_name(raw, "issuer"))
    now = time.time()
    for field, key in (("notBefore", "starts"), ("notAfter", "expires")):
        value = raw.get(field)
        if not value:
            continue
        out[key] = value
        try:
            out[key + "_at"] = ssl.cert_time_to_seconds(value)
        except (ValueError, TypeError):
            pass
    expires_at = out.get("expires_at")
    if isinstance(expires_at, (int, float)):
        out["days_left"] = int((expires_at - now) // 86400)
        out["expired"] = expires_at <= now
    starts_at = out.get("starts_at")
    if isinstance(starts_at, (int, float)):
        out["not_yet_valid"] = starts_at > now
    try:
        out["count"] = len(split_pem_certs(_read_text(Path(cert_path))))
    except Exception:
        out["count"] = 1
    return out


def describe(cert: str) -> Dict[str, str]:
    """Backwards-compatible view of :func:`inspect` -- strings only."""
    info = inspect(cert)
    out: Dict[str, str] = {}
    if info.get("name"):
        out["name"] = str(info["name"])
    names = info.get("names") or []
    if names:
        out["names"] = ", ".join(str(n) for n in names)  # type: ignore[union-attr]
    if info.get("expires"):
        out["expires"] = str(info["expires"])
    if info.get("days_left") is not None:
        out["days_left"] = str(info["days_left"])
    return out


def key_matches_cert(cert: str, key: str) -> Tuple[bool, str]:
    """Would OpenSSL serve with this pair exactly as the files stand?

    The same call the server makes, made early: a mismatched pair fails here,
    where the message can name the two files, rather than during start-up
    where it is an SSLError about key values.

    Note that OpenSSL checks the key against the *first* certificate in the
    file and nothing else, so a chain that arrives intermediate-first fails
    this even though every certificate in it is right.  :func:`find_leaf` is
    the one to ask when that matters.
    """
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(certfile=cert, keyfile=key)
        return True, ""
    except (ssl.SSLError, OSError, ValueError) as exc:
        detail = getattr(exc, "reason", "") or str(exc)
        return False, str(detail)


def find_leaf(cert: str, key: str) -> Tuple[int, str]:
    """Which certificate in ``cert`` this key belongs to, and why not if none.

    Returns the index of the matching certificate, or ``-1``.  Index 0 is the
    ordinary answer and costs one load; anything else means the download put
    the intermediates before the leaf, which every desktop browser forgives
    and phones do not -- so it is worth finding rather than rejecting, and
    :func:`build_chain` puts the order right.
    """
    if not _readable(cert, key):
        return -1, "not readable"
    ok, why = key_matches_cert(cert, key)
    if ok:
        return 0, ""
    blocks = split_pem_certs(_read_text(Path(cert)))
    if len(blocks) < 2:
        return -1, why
    tmpdir = tempfile.mkdtemp(prefix="bh-leaf-")
    try:
        for index, block in enumerate(blocks[1:], start=1):
            candidate = os.path.join(tmpdir, "c%d.pem" % index)
            with open(candidate, "w", encoding="utf-8") as fh:
                fh.write(block)
            if key_matches_cert(candidate, key)[0]:
                return index, ""
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return -1, why


# ----------------------------------------------------------- chain assembly
def _ordered_chain(blocks: Sequence[str], leaf_first: Optional[str] = None
                   ) -> Optional[List[str]]:
    """Order certificates leaf -> issuer -> issuer, or None if unsure.

    A browser walks the chain in the order it is sent, so a bundle whose
    intermediates arrive before the leaf is rejected by strict clients even
    though every certificate in it is fine.  Ordering needs each block's
    subject and issuer, and decoding a block means writing it out first --
    so this is done once, at start-up, and never per connection.
    """
    if len(blocks) <= 1:
        return list(blocks)
    parsed: List[Tuple[str, str, str]] = []           # (block, subject, issuer)
    tmpdir = tempfile.mkdtemp(prefix="bh-chain-")
    try:
        for index, block in enumerate(blocks):
            path = os.path.join(tmpdir, "c%d.pem" % index)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(block)
            raw = _decode(path)
            if not raw:
                return None
            parsed.append((block, _full_name(raw, "subject"),
                           _full_name(raw, "issuer")))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    if any(not subject or not issuer for _b, subject, issuer in parsed):
        return None

    by_subject = {item[1]: item for item in parsed}
    if len(by_subject) != len(parsed):
        return list(blocks)                # duplicate subjects: leave it alone
    issuers = {issuer for _b, _s, issuer in parsed}
    if leaf_first is not None:
        head = next((item for item in parsed if item[0].strip() ==
                     leaf_first.strip()), None)
    else:
        head = None
    if head is None:
        # The leaf is the one certificate nothing else was issued by.
        leaves = [item for item in parsed if item[1] not in issuers]
        if len(leaves) != 1:
            return None
        head = leaves[0]

    chain = [head]
    used = {head[1]}
    while True:
        issuer = chain[-1][2]
        if issuer in used:                 # self-signed root, or a loop
            break
        nxt = by_subject.get(issuer)
        if nxt is None:
            break
        chain.append(nxt)
        used.add(nxt[1])
    if len(chain) != len(parsed):
        return None                        # something is unrelated: don't guess
    return [item[0] for item in chain]


def _write_assembled(name: str, blocks: Sequence[str]) -> str:
    ASSEMBLED_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSEMBLED_DIR / ("%s.fullchain.pem" % name)
    body = "".join(block if block.endswith("\n") else block + "\n"
                   for block in blocks)
    path.write_text(body, encoding="utf-8")
    try:
        os.chmod(path, 0o644)
    except OSError:
        pass
    return str(path)


def build_chain(cert_path: str, chain_path: str = "", name: str = "",
                leaf_index: int = 0) -> Tuple[str, str]:
    """The file to actually serve, and a note about what had to be done.

    The certificate as downloaded is used untouched whenever it is already a
    correctly ordered chain -- which is the common case and the one worth not
    meddling with.  A file is only written when the intermediates live
    somewhere else, or when the order would make a phone reject the site.

    ``leaf_index`` is where the site's own certificate sits in ``cert_path``,
    as :func:`find_leaf` reports it; it is 0 for every well-formed bundle.
    """
    leaf_blocks = split_pem_certs(_read_text(Path(cert_path)))
    if not leaf_blocks:
        return cert_path, ""
    if not 0 <= leaf_index < len(leaf_blocks):
        leaf_index = 0
    extra_blocks: List[str] = []
    if chain_path and _readable(chain_path):
        extra_blocks = split_pem_certs(_read_text(Path(chain_path)))

    seen = set()
    blocks: List[str] = []
    for block in list(leaf_blocks) + list(extra_blocks):
        stripped = block.strip()
        if stripped in seen:
            continue
        seen.add(stripped)
        blocks.append(block)

    ordered = _ordered_chain(blocks, leaf_first=leaf_blocks[leaf_index])
    stem = name or Path(cert_path).stem.split(".")[0] or "site"

    if ordered is None:
        # The chain could not be read well enough to order it.  Move the leaf
        # to the front anyway if it is known not to be there -- OpenSSL will
        # not serve a file that starts with anything else.
        if leaf_index:
            ordered = ([blocks[leaf_index]]
                       + [b for i, b in enumerate(blocks) if i != leaf_index])
            return (_write_assembled(stem, ordered),
                    "leaf certificate moved to the front")
        if len(blocks) == len(leaf_blocks):
            return cert_path, ""           # nothing added, nothing to say
        return (_write_assembled(stem, blocks),
                "intermediates from %s appended" % Path(chain_path).name)
    if len(blocks) == len(leaf_blocks) and ordered == list(leaf_blocks):
        return cert_path, ""               # already exactly right
    note = ("chain re-ordered leaf first"
            if len(blocks) == len(leaf_blocks)
            else "intermediates from %s merged in" % Path(chain_path).name)
    return _write_assembled(stem, ordered), note


# ----------------------------------------------------------- bundle discovery
def _bundle_dirs(extra: str = "") -> List[Path]:
    """Where a downloaded bundle is looked for, in the order it is trusted."""
    dirs: List[Path] = []
    for candidate in (extra, os.environ.get("BLOCKHAVEN_CERT_DIR", "")):
        if candidate:
            dirs.append(Path(candidate).expanduser())
    dirs.append(config.CERT_DIR)
    dirs.append(config.DATA_DIR / "certs")
    dirs.append(Path("/etc/blockhaven/certs"))
    out: List[Path] = []
    for path in dirs:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved not in out:
            out.append(resolved)
    return out


def _bundle_files(root: Path) -> List[Path]:
    """Every plausible PEM under ``root``, a few levels deep, cheapest first."""
    found: List[Path] = []
    stack: List[Tuple[Path, int]] = [(root, 0)]
    while stack and len(found) < MAX_BUNDLE_FILES:
        directory, depth = stack.pop(0)
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.is_dir():
                    if depth + 1 < BUNDLE_DEPTH and not entry.name.startswith("."):
                        stack.append((entry, depth + 1))
                    continue
                if not entry.is_file() or entry.name.startswith("."):
                    continue
                if entry.stat().st_size > MAX_PEM_BYTES:
                    continue
            except OSError:
                continue
            # fullchain.pem.1 and friends are the copies install_cert.py keeps
            # of what it replaced.  They are there to be restored by hand, not
            # to be served, and a renewal should not change which certificate
            # wins just by existing.
            if entry.suffix[1:].isdigit() and "." in entry.stem:
                continue
            found.append(entry)
            if len(found) >= MAX_BUNDLE_FILES:
                break
    return found


def _rank(name: str, known: Sequence[str]) -> int:
    lowered = name.lower()
    for index, candidate in enumerate(known):
        if lowered == candidate:
            return index
    for index, candidate in enumerate(known):
        if lowered.endswith(candidate):
            return len(known) + index
    return 2 * len(known)


def scan_bundle(directory: Path) -> List[Dict[str, str]]:
    """Cert/key pairs in ``directory``, best first.

    Files are classified by what is *in* them rather than by what they are
    called, so a bundle whose provider invented its own names still works;
    the names only decide the order things are tried in.
    """
    certs: List[Tuple[int, int, Path, int]] = []   # rank, -count, path, count
    keys: List[Tuple[int, Path]] = []
    chains: List[Tuple[int, Path, int]] = []
    for path in _bundle_files(directory):
        text = _read_text(path)
        if not text:
            continue
        blocks = split_pem_certs(text)
        if _has_private_key(text):
            if any(bad in path.name.lower() for bad in _NOT_A_KEY):
                continue
            keys.append((_rank(path.name, _KEY_NAMES), path))
            if blocks:
                # A combined PEM: usable as its own certificate file too.
                certs.append((_rank(path.name, _CERT_NAMES), -len(blocks),
                              path, len(blocks)))
            continue
        if not blocks:
            continue
        certs.append((_rank(path.name, _CERT_NAMES), -len(blocks), path,
                      len(blocks)))
        chains.append((_rank(path.name, _CHAIN_NAMES), path, len(blocks)))

    certs.sort(key=lambda item: (item[0], item[1], str(item[2])))
    keys.sort(key=lambda item: (item[0], str(item[1])))
    chains.sort(key=lambda item: (item[0], str(item[1])))

    pairs: List[Dict[str, str]] = []
    for _rank_c, _neg, cert_path, count in certs:
        for _rank_k, key_path in keys:
            leaf_index, _why = find_leaf(str(cert_path), str(key_path))
            if leaf_index < 0:
                continue
            chain_path = ""
            if count == 1:
                # Leaf on its own: the intermediates are in another file, and
                # without them every phone that visits gets a warning.
                for _rank_ch, candidate, _n in chains:
                    if candidate == cert_path:
                        continue
                    if _rank(candidate.name, _CHAIN_NAMES) < 2 * len(_CHAIN_NAMES):
                        chain_path = str(candidate)
                        break
            pairs.append({"cert": str(cert_path), "key": str(key_path),
                          "chain": chain_path, "leaf_index": str(leaf_index)})
            break
    return pairs


# ------------------------------------------------------------------ locating
def letsencrypt_paths(domain: str) -> Tuple[str, str]:
    live = LETSENCRYPT / domain
    return str(live / "fullchain.pem"), str(live / "privkey.pem")


def self_signed_paths(domain: str) -> Tuple[str, str]:
    name = domain or "localhost"
    return (str(SELF_SIGNED_DIR / ("%s.crt" % name)),
            str(SELF_SIGNED_DIR / ("%s.key" % name)))


def _candidates(domain: str, cert: str, key: str, cert_dir: str
                ) -> List[Dict[str, str]]:
    """Every pair worth considering, in order of how explicit it was."""
    found: List[Dict[str, str]] = []
    if cert or key:
        found.append({"cert": cert, "key": key, "chain": "",
                      "source": "given on the command line"})
        return found
    for directory in _bundle_dirs(cert_dir):
        if not directory.is_dir():
            continue
        for pair in scan_bundle(directory):
            pair["source"] = "bundle in %s" % _pretty(Path(pair["cert"]).parent)
            found.append(pair)
    names = [domain] if domain else []
    try:
        names += sorted(p.name for p in LETSENCRYPT.iterdir() if p.is_dir())
    except OSError:
        pass
    for name in names:
        le_cert, le_key = letsencrypt_paths(name)
        if not _readable(le_cert, le_key):
            continue
        if any(pair["cert"] == le_cert for pair in found):
            continue
        found.append({"cert": le_cert, "key": le_key, "chain": "",
                      "source": "Let's Encrypt (%s)" % (LETSENCRYPT / name)})
    return found


def _pretty(path: Path) -> str:
    """A path relative to the project when it is inside it, absolute if not."""
    try:
        return str(path.resolve().relative_to(config.BASE_DIR))
    except (ValueError, OSError):
        return str(path)


def evaluate(pair: Dict[str, str], domain: str = "") -> Dict[str, object]:
    """Check one candidate and describe what is right and wrong with it."""
    out: Dict[str, object] = dict(pair)
    problems: List[str] = []
    warnings: List[str] = []
    out["problems"], out["warnings"] = problems, warnings
    out["usable"] = False

    cert, key = pair.get("cert", ""), pair.get("key", "")
    if not cert or not key:
        problems.append("no certificate and private key to check")
        return out
    if not _readable(cert, key):
        missing = [p for p in (cert, key)
                   if not p or not os.path.isfile(p)]
        unreadable = [p for p in (cert, key)
                      if p and os.path.isfile(p) and not os.access(p, os.R_OK)]
        if missing:
            problems.append("not there: %s" % ", ".join(missing))
        if unreadable:
            problems.append("not readable by this user: %s"
                            % ", ".join(unreadable))
        return out

    try:
        leaf_index = int(pair.get("leaf_index") or 0)
    except (TypeError, ValueError):
        leaf_index = 0
    if "leaf_index" not in pair:
        leaf_index, why = find_leaf(cert, key)
        if leaf_index < 0:
            problems.append("the private key does not go with this "
                            "certificate" + (" (%s)" % why if why else ""))
            return out
    if leaf_index:
        warnings.append("the chain arrived with the intermediates before the "
                        "site's own certificate; serving it the right way up")

    serve_cert, note = cert, ""
    try:
        serve_cert, note = build_chain(cert, pair.get("chain", ""),
                                       name=domain or "", leaf_index=leaf_index)
    except OSError as exc:
        warnings.append("could not assemble the chain (%s); "
                        "serving the certificate as downloaded" % exc)
        serve_cert = cert
    out["serve_cert"] = serve_cert
    if note:
        out["chain_note"] = note

    info = inspect(serve_cert)
    out["info"] = info
    if not info:
        warnings.append("could not read the certificate's details")
        out["usable"] = True
        return out

    if info.get("expired"):
        problems.append("expired on %s" % info.get("expires", "?"))
    elif info.get("not_yet_valid"):
        problems.append("not valid until %s" % info.get("starts", "?"))
    else:
        days = info.get("days_left")
        if isinstance(days, int) and days <= 14:
            warnings.append("expires in %d day%s (%s)"
                            % (days, "" if days == 1 else "s",
                               info.get("expires", "?")))
    if info.get("self_signed"):
        warnings.append("self-signed: every browser will warn")
    if int(info.get("count") or 1) < 2 and not info.get("self_signed"):
        warnings.append("no intermediate certificate in the chain -- desktop "
                        "browsers paper over this, phones do not")

    names = [str(n) for n in (info.get("names") or [])]
    out["covers"] = names
    if domain and names:
        if any(host_matches(n, domain) for n in names):
            out["matches_domain"] = True
        else:
            out["matches_domain"] = False
            problems.append("does not cover %s (it covers %s)"
                            % (domain, ", ".join(names)))
    out["usable"] = not problems
    return out


def locate(domain: str = "", cert: str = "", key: str = "",
           allow_self_signed: bool = False, cert_dir: str = "",
           checked: Optional[List[Dict[str, object]]] = None
           ) -> Optional[Dict[str, str]]:
    """The certificate to serve with, or None if there is not one yet.

    Returns ``{"cert", "key", "source", ...}`` where ``cert`` is the file to
    hand OpenSSL -- the chain as downloaded when that is already right, and
    the re-assembled one when it was not.  ``source`` is for the operator: it
    is the difference between "this is the real certificate for your domain"
    and "this is the throwaway one, every browser will warn".

    ``checked`` collects the verdict on every candidate, including the ones
    passed over, so ``--tls-check`` can explain itself.
    """
    results: List[Dict[str, object]] = []
    for pair in _candidates(domain, cert, key, cert_dir):
        verdict = evaluate(pair, domain)
        results.append(verdict)
    if checked is not None:
        checked.extend(results)

    if (cert or key) and results and not results[0].get("usable"):
        raise TLSError("--cert/--key: %s"
                       % "; ".join(str(p) for p in results[0]["problems"]))  # type: ignore[index]

    usable = [r for r in results if r.get("usable")]
    if usable:
        # Prefer one that actually covers the name the site answers to, then
        # the one that lasts longest -- a renewed bundle beside the old one
        # should win without anybody deleting the old one first.
        def score(item: Dict[str, object]) -> Tuple[int, int]:
            info = item.get("info") or {}
            days = info.get("days_left") if isinstance(info, dict) else None
            return (0 if item.get("matches_domain") is not False else 1,
                    -int(days) if isinstance(days, int) else 0)

        best = sorted(usable, key=score)[0]
        chosen = {
            "cert": str(best.get("serve_cert") or best["cert"]),
            "key": str(best["key"]),
            "source": str(best.get("source", "")),
            "origin_cert": str(best["cert"]),
        }
        if best.get("chain_note"):
            chosen["chain_note"] = str(best["chain_note"])
        if best.get("warnings"):
            chosen["warnings"] = "; ".join(str(w) for w in best["warnings"])  # type: ignore[union-attr]
        names = best.get("covers") or []
        if names:
            chosen["covers"] = ", ".join(str(n) for n in names)  # type: ignore[union-attr]
            chosen["domain"] = primary_name(list(names), domain)  # type: ignore[arg-type]
        return chosen

    if allow_self_signed:
        ss_cert, ss_key = self_signed_paths(domain)
        if not _readable(ss_cert, ss_key):
            make_self_signed(domain)
        # No "warnings" here: the caller keys off source == "self-signed"
        # and says so once, rather than twice in the same status block.
        return {"cert": ss_cert, "key": ss_key, "source": "self-signed",
                "origin_cert": ss_cert, "domain": domain}
    return None


def primary_name(names: Sequence[str], preferred: str = "") -> str:
    """The name to send visitors to: the one asked for, else the plainest.

    A wildcard is never it -- redirecting somebody to ``*.example.com`` is not
    a URL -- so the bare name wins, and the shortest one after that.
    """
    if preferred and any(host_matches(n, preferred) for n in names):
        return preferred
    plain = [n for n in names if not n.startswith("*.")]
    if plain:
        return sorted(plain, key=lambda n: (n.count("."), len(n)))[0]
    for name in names:
        if name.startswith("*."):
            return name[2:]
    return preferred


# ---------------------------------------------------------------- self-signed
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


# --------------------------------------------------------------- operator aid
def certbot_hint(domain: str, webroot: Optional[Path] = None) -> str:
    """The exact command that turns a working port 80 into a certificate."""
    root = webroot or config.ACME_WEBROOT
    name = domain or "your-domain.example"
    return (
        "  sudo certbot certonly --webroot -w %s -d %s\n"
        "then restart with --domain %s.  Leave the server running while\n"
        "certbot works: it answers the challenge on port 80 itself."
        % (root, name, name))


def bundle_hint() -> str:
    """What to do with a certificate downloaded from a registrar or host."""
    return (
        "  python3 tools/install_cert.py <the-bundle.zip>\n"
        "unpacks a downloaded certificate into %s/ and checks it over; after\n"
        "that ./run.sh finds it by itself.  Any folder holding the bundle\n"
        "works in place of the zip." % _pretty(config.CERT_DIR))


def report(domain: str = "", cert: str = "", key: str = "",
           cert_dir: str = "") -> Tuple[bool, str]:
    """A human-readable account of what was found and what it is worth.

    This is ``main.py --tls-check``: it answers "why is my site still not
    secure" without starting the server or binding a port.
    """
    lines: List[str] = []
    checked: List[Dict[str, object]] = []
    try:
        chosen = locate(domain, cert, key, allow_self_signed=False,
                        cert_dir=cert_dir, checked=checked)
    except TLSError as exc:
        chosen = None
        lines.append("  %s" % exc)

    lines.append("Looked in:")
    for directory in _bundle_dirs(cert_dir):
        mark = "found" if directory.is_dir() else "no such directory"
        lines.append("  %-44s %s" % (_pretty(directory), mark))
    lines.append("  %-44s %s" % (str(LETSENCRYPT),
                                 "found" if LETSENCRYPT.is_dir()
                                 else "no such directory"))
    lines.append("")

    if not checked:
        lines.append("No certificate found at all, so the site can only be "
                     "served over plain HTTP.")
        lines.append("")
        lines.append(bundle_hint())
        lines.append("")
        lines.append("Or, to have Let's Encrypt issue one directly:")
        lines.append(certbot_hint(domain))
        return False, "\n".join(lines)

    lines.append("Certificates found:")
    for item in checked:
        info = item.get("info") or {}
        head = "  %s" % _pretty(Path(str(item["cert"])))
        lines.append(head)
        lines.append("      source    %s" % item.get("source", "?"))
        lines.append("      key       %s" % _pretty(Path(str(item["key"]))))
        if isinstance(info, dict) and info.get("names"):
            lines.append("      covers    %s"
                         % ", ".join(str(n) for n in info["names"]))
        if isinstance(info, dict) and info.get("issuer"):
            lines.append("      issued by %s" % info["issuer"])
        if isinstance(info, dict) and info.get("expires"):
            days = info.get("days_left")
            lines.append("      expires   %s%s"
                         % (info["expires"],
                            " (%d days)" % days if isinstance(days, int) else ""))
        if isinstance(info, dict) and info.get("count"):
            count = int(info["count"])
            lines.append("      chain     %d certificate%s%s"
                         % (count, "" if count == 1 else "s",
                            " -- leaf only" if count == 1 else ""))
        if item.get("chain_note"):
            lines.append("      fixed up  %s" % item["chain_note"])
        for problem in item.get("problems") or []:            # type: ignore[union-attr]
            lines.append("      PROBLEM   %s" % problem)
        for warning in item.get("warnings") or []:            # type: ignore[union-attr]
            lines.append("      note      %s" % warning)
        lines.append("      verdict   %s"
                     % ("usable" if item.get("usable") else "not usable"))
        lines.append("")

    if chosen:
        lines.append("HTTPS will use %s" % _pretty(Path(chosen["cert"])))
        if chosen.get("domain"):
            lines.append("and the site will answer as https://%s"
                         % chosen["domain"])
        return True, "\n".join(lines)
    lines.append("Nothing usable, so the site would be served over plain HTTP.")
    lines.append("")
    lines.append(bundle_hint())
    return False, "\n".join(lines)
