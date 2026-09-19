#!/usr/bin/env python3
"""Tests for certificate discovery, chain assembly and name matching.

These do not need a server or a network: openssl mints throwaway certificates
into a temporary directory and the discovery code is pointed at them.  What is
being proved is the set of things that silently make a browser say "Not
secure", each of which is easy to ship and hard to notice:

* a bundle is found whatever its provider called the files, and however deep
  in the folder it was unzipped into it sits,
* ``public.key.pem`` -- which ships in most bundles and is not a private key
  -- is not mistaken for one,
* a leaf certificate with its intermediates in a separate file is assembled
  into one chain, leaf first,
* a chain that arrives in the wrong order is put right,
* a key that does not belong to the certificate is refused rather than served,
* an expired certificate, and one that does not cover the domain, are both
  reported instead of quietly used,
* wildcard matching follows the rule browsers follow.

    python3 tools/tlstests.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

PASSED: List[str] = []
FAILED: List[str] = []


def check(name: str, condition: bool, detail: object = "") -> bool:
    if condition:
        PASSED.append(name)
        print("  PASS  %s" % name)
    else:
        FAILED.append(name)
        print("  FAIL  %s  %s" % (name, str(detail)[:300]))
    return bool(condition)


# ------------------------------------------------------------- certificate CA
def _run(*cmd: str) -> None:
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError("%s failed: %s"
                           % (cmd[0], result.stderr.decode("utf-8", "replace")))


def make_ca(directory: Path, name: str = "Test Root") -> Tuple[Path, Path]:
    """A throwaway certificate authority to issue the test leaves from."""
    key = directory / "ca.key"
    cert = directory / "ca.crt"
    _run("openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
         "-keyout", str(key), "-out", str(cert), "-days", "30",
         "-subj", "/CN=%s" % name)
    return cert, key


def issue(directory: Path, ca_cert: Path, ca_key: Path, common: str,
          names: Optional[List[str]] = None, days: int = 30,
          start_days_ago: int = 1) -> Tuple[Path, Path]:
    """A leaf certificate signed by the test CA, valid for ``days``."""
    stem = common.replace("*", "wildcard").replace(".", "_")
    key = directory / ("%s.key" % stem)
    csr = directory / ("%s.csr" % stem)
    cert = directory / ("%s.crt" % stem)
    alt = ",".join("DNS:%s" % n for n in (names or [common]))
    _run("openssl", "req", "-newkey", "rsa:2048", "-nodes", "-keyout",
         str(key), "-out", str(csr), "-subj", "/CN=%s" % common)
    extfile = directory / ("%s.ext" % stem)
    extfile.write_text("subjectAltName=%s\n" % alt)
    _run("openssl", "x509", "-req", "-in", str(csr), "-CA", str(ca_cert),
         "-CAkey", str(ca_key), "-CAcreateserial", "-out", str(cert),
         "-days", str(days), "-extfile", str(extfile))
    csr.unlink(missing_ok=True)
    extfile.unlink(missing_ok=True)
    return cert, key


# ------------------------------------------------------------------- the tests
def test_name_matching(tls) -> None:
    print("== wildcard and name matching ==")
    check("exact name matches", tls.host_matches("example.com", "example.com"))
    check("case is ignored", tls.host_matches("Example.COM", "example.com"))
    check("trailing dot is ignored",
          tls.host_matches("example.com.", "example.com"))
    check("wildcard covers one label",
          tls.host_matches("*.example.com", "www.example.com"))
    check("wildcard does not cover the apex",
          not tls.host_matches("*.example.com", "example.com"))
    check("wildcard does not cover two labels",
          not tls.host_matches("*.example.com", "a.b.example.com"))
    check("a different domain does not match",
          not tls.host_matches("*.example.com", "www.example.net"))
    check("a suffix is not a match",
          not tls.host_matches("example.com", "notexample.com"))
    check("empty matches nothing", not tls.host_matches("", "example.com"))
    print("")
    print("== the name visitors are sent to ==")
    check("the bare name beats the wildcard",
          tls.primary_name(["*.example.com", "example.com"]) == "example.com")
    check("a wildcard alone becomes its parent",
          tls.primary_name(["*.example.com"]) == "example.com")
    check("the name asked for wins when it is covered",
          tls.primary_name(["*.example.com", "example.com"],
                           "shop.example.com") == "shop.example.com")
    check("a name not covered does not win",
          tls.primary_name(["example.com"], "other.net") == "example.com")
    print("")


def test_discovery(tls, work: Path, ca_cert: Path, ca_key: Path) -> None:
    print("== finding a downloaded bundle ==")

    # A registrar's layout, unzipped into a subfolder, as it arrives.
    bundle = work / "certs-registrar" / "example.com-ssl-bundle"
    bundle.mkdir(parents=True)
    cert, key = issue(work, ca_cert, ca_key, "example.com",
                      ["example.com", "*.example.com"])
    fullchain = cert.read_text() + ca_cert.read_text()
    (bundle / "domain.cert.pem").write_text(fullchain)
    (bundle / "private.key.pem").write_text(key.read_text())
    # The public key ships alongside and is not the private one.
    _run("openssl", "rsa", "-in", str(key), "-pubout",
         "-out", str(bundle / "public.key.pem"))

    pairs = tls.scan_bundle(work / "certs-registrar")
    check("a bundle one folder down is found", len(pairs) == 1, pairs)
    if pairs:
        check("the certificate is the right file",
              Path(pairs[0]["cert"]).name == "domain.cert.pem", pairs[0])
        check("public.key.pem is not taken for the private key",
              Path(pairs[0]["key"]).name == "private.key.pem", pairs[0])

    verdict = tls.evaluate(pairs[0] if pairs else {}, "www.example.com")
    check("the bundle is usable", verdict.get("usable"), verdict.get("problems"))
    check("the wildcard covers a subdomain",
          verdict.get("matches_domain") is True, verdict)
    check("both names are reported",
          set(verdict.get("covers") or []) == {"example.com", "*.example.com"},
          verdict.get("covers"))
    print("")


def test_chain_assembly(tls, work: Path, ca_cert: Path, ca_key: Path) -> None:
    print("== assembling and ordering the chain ==")

    # cPanel's shape: the leaf alone, intermediates in their own file.
    split = work / "certs-split"
    split.mkdir()
    cert, key = issue(work, ca_cert, ca_key, "split.example.com")
    (split / "certificate.crt").write_text(cert.read_text())
    (split / "ca_bundle.crt").write_text(ca_cert.read_text())
    (split / "private.key").write_text(key.read_text())

    pairs = tls.scan_bundle(split)
    check("a split bundle is found", len(pairs) == 1, pairs)
    if pairs:
        check("the intermediate file is picked up",
              Path(pairs[0]["chain"]).name == "ca_bundle.crt", pairs[0])
    verdict = tls.evaluate(pairs[0] if pairs else {}, "split.example.com")
    served = Path(str(verdict.get("serve_cert", "")))
    check("a chain was assembled to serve",
          served.exists() and served != Path(str(verdict.get("cert"))), served)
    blocks = tls.split_pem_certs(served.read_text()) if served.exists() else []
    check("the assembled chain holds both certificates", len(blocks) == 2,
          len(blocks))
    check("the leaf comes first",
          bool(blocks) and blocks[0].strip() ==
          tls.split_pem_certs(cert.read_text())[0].strip())
    check("the assembled chain still loads with the key",
          tls.key_matches_cert(str(served), pairs[0]["key"])[0] if pairs
          else False)

    # The same certificates, delivered in the wrong order in one file.
    backwards = work / "certs-backwards"
    backwards.mkdir()
    (backwards / "fullchain.pem").write_text(ca_cert.read_text()
                                             + cert.read_text())
    (backwards / "privkey.pem").write_text(key.read_text())
    pairs = tls.scan_bundle(backwards)
    verdict = tls.evaluate(pairs[0] if pairs else {}, "split.example.com")
    served = Path(str(verdict.get("serve_cert", "")))
    blocks = tls.split_pem_certs(served.read_text()) if served.exists() else []
    check("a backwards chain is re-ordered leaf first",
          bool(blocks) and blocks[0].strip() ==
          tls.split_pem_certs(cert.read_text())[0].strip(),
          verdict.get("chain_note"))
    check("re-ordering is reported", bool(verdict.get("chain_note")),
          verdict)

    # A chain that is already right is served untouched.
    good = work / "certs-good"
    good.mkdir()
    (good / "fullchain.pem").write_text(cert.read_text() + ca_cert.read_text())
    (good / "privkey.pem").write_text(key.read_text())
    pairs = tls.scan_bundle(good)
    verdict = tls.evaluate(pairs[0] if pairs else {}, "split.example.com")
    check("a correct chain is left alone",
          str(verdict.get("serve_cert")) == str(good / "fullchain.pem"),
          verdict.get("serve_cert"))
    print("")


def test_rejections(tls, work: Path, ca_cert: Path, ca_key: Path) -> None:
    print("== what should be refused ==")

    # A key from a different certificate: the classic mixed-up download.
    mixed = work / "certs-mixed"
    mixed.mkdir()
    cert_a, _key_a = issue(work, ca_cert, ca_key, "a.example.com")
    _cert_b, key_b = issue(work, ca_cert, ca_key, "b.example.com")
    (mixed / "fullchain.pem").write_text(cert_a.read_text())
    (mixed / "privkey.pem").write_text(key_b.read_text())
    check("a mismatched pair is not offered", tls.scan_bundle(mixed) == [],
          tls.scan_bundle(mixed))
    verdict = tls.evaluate({"cert": str(mixed / "fullchain.pem"),
                            "key": str(mixed / "privkey.pem")},
                           "a.example.com")
    check("a mismatched pair is not usable", not verdict.get("usable"))
    check("and it says the key is wrong",
          any("private key" in p for p in verdict.get("problems") or []),
          verdict.get("problems"))

    # Expired.
    old = work / "certs-expired"
    old.mkdir()
    expired_cert, expired_key = issue(work, ca_cert, ca_key,
                                      "old.example.com", days=-1)
    (old / "fullchain.pem").write_text(expired_cert.read_text())
    (old / "privkey.pem").write_text(expired_key.read_text())
    verdict = tls.evaluate(tls.scan_bundle(old)[0], "old.example.com")
    check("an expired certificate is not usable", not verdict.get("usable"))
    check("and it says so",
          any("expired" in p for p in verdict.get("problems") or []),
          verdict.get("problems"))

    # Right certificate, wrong site.
    other = work / "certs-other"
    other.mkdir()
    other_cert, other_key = issue(work, ca_cert, ca_key, "other.example.net")
    (other / "fullchain.pem").write_text(other_cert.read_text())
    (other / "privkey.pem").write_text(other_key.read_text())
    verdict = tls.evaluate(tls.scan_bundle(other)[0], "example.com")
    check("a certificate for another name is not usable",
          not verdict.get("usable"))
    check("and it names what it does cover",
          any("does not cover" in p for p in verdict.get("problems") or []),
          verdict.get("problems"))

    # Nothing at all.
    empty = work / "certs-empty"
    empty.mkdir(exist_ok=True)
    check("an empty folder yields nothing", tls.scan_bundle(empty) == [])
    print("")


def test_locate(tls, work: Path, ca_cert: Path, ca_key: Path) -> None:
    print("== choosing between certificates ==")
    many = work / "certs-many"
    many.mkdir()
    short = many / "expiring-soon"
    short.mkdir()
    cert_s, key_s = issue(work, ca_cert, ca_key, "example.com", days=3)
    (short / "fullchain.pem").write_text(cert_s.read_text() + ca_cert.read_text())
    (short / "privkey.pem").write_text(key_s.read_text())
    fresh = many / "renewed"
    fresh.mkdir()
    cert_f, key_f = issue(work, ca_cert, ca_key, "example.com", days=60)
    (fresh / "fullchain.pem").write_text(cert_f.read_text() + ca_cert.read_text())
    (fresh / "privkey.pem").write_text(key_f.read_text())

    chosen = tls.locate("example.com", cert_dir=str(many))
    check("a certificate is chosen", bool(chosen))
    if chosen:
        info = tls.inspect(chosen["cert"])
        days = info.get("days_left")
        check("the one that lasts longest wins",
              isinstance(days, int) and days > 30, days)
        check("the domain is read off the certificate",
              chosen.get("domain") == "example.com", chosen.get("domain"))

    # An unreadable key is a problem, not a crash.
    locked = work / "certs-locked"
    locked.mkdir()
    cert_l, key_l = issue(work, ca_cert, ca_key, "locked.example.com")
    (locked / "fullchain.pem").write_text(cert_l.read_text())
    (locked / "privkey.pem").write_text(key_l.read_text())
    verdict = tls.evaluate({"cert": str(locked / "fullchain.pem"),
                            "key": str(locked / "missing.pem")},
                           "locked.example.com")
    check("a missing key is reported, not raised",
          not verdict.get("usable")
          and any("not there" in p for p in verdict.get("problems") or []),
          verdict.get("problems"))

    check("no certificate anywhere means None",
          tls.locate("example.com", cert_dir=str(work / "certs-empty")) is None)
    print("")


def test_installer(work: Path, ca_cert: Path, ca_key: Path) -> None:
    print("== the installer ==")
    import zipfile
    from app.http import tls as tls_support
    from tools import install_cert

    staging = work / "to-zip" / "example.com-ssl-bundle"
    staging.mkdir(parents=True)
    cert, key = issue(work, ca_cert, ca_key, "install.example.com")
    (staging / "domain.cert.pem").write_text(cert.read_text())
    (staging / "intermediate.cert.pem").write_text(ca_cert.read_text())
    (staging / "private.key.pem").write_text(key.read_text())
    archive = work / "bundle.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        for path in staging.iterdir():
            zf.write(path, "example.com-ssl-bundle/%s" % path.name)

    destination = work / "installed"
    code = install_cert.main([str(archive), "--into", str(destination),
                              "--domain", "install.example.com"])
    check("installing from a zip succeeds", code == 0, code)
    check("it writes fullchain.pem", (destination / "fullchain.pem").exists())
    check("it writes privkey.pem", (destination / "privkey.pem").exists())
    if (destination / "privkey.pem").exists():
        mode = (destination / "privkey.pem").stat().st_mode & 0o777
        check("the key is not readable by everybody", mode == 0o600,
              oct(mode))
    check("the installed pair loads",
          tls_support.key_matches_cert(str(destination / "fullchain.pem"),
                                       str(destination / "privkey.pem"))[0])
    check("the intermediate came with it",
          len(tls_support.split_pem_certs(
              (destination / "fullchain.pem").read_text())) == 2)

    # Installing again keeps the one it replaces.
    code = install_cert.main([str(archive), "--into", str(destination),
                              "--domain", "install.example.com"])
    check("re-installing succeeds", code == 0, code)
    check("the previous certificate is kept as .1",
          (destination / "fullchain.pem.1").exists())

    # The bundle is very often left in certs/ -- installed from there, and
    # then scanned on every start from then on.
    print("")
    print("== installing from a zip inside certs/ ==")
    live = work / "live-certs"
    live.mkdir()
    in_place = live / "scrpt.zip"
    shutil.copyfile(archive, in_place)
    code = install_cert.main([str(in_place), "--into", str(live),
                              "--domain", "install.example.com"])
    check("installing from a zip in the destination succeeds", code == 0, code)
    check("the zip it was given is left alone", in_place.exists())
    check("the certificate landed beside it",
          (live / "fullchain.pem").exists() and (live / "privkey.pem").exists())

    pairs = tls_support.scan_bundle(live)
    check("exactly one certificate is found next to the zip",
          len(pairs) == 1, [p["cert"] for p in pairs])
    if pairs:
        check("and it is the installed one, not the archive",
              Path(pairs[0]["cert"]).name == "fullchain.pem", pairs[0])
    chosen = tls_support.locate("install.example.com", cert_dir=str(live))
    check("the server would serve the installed certificate",
          bool(chosen) and Path(chosen["cert"]).name == "fullchain.pem",
          chosen)

    # A zip written without compression carries its PEM files verbatim, so
    # reading it as text finds real certificate blocks in it.
    stored_dir = work / "stored-zip"
    stored_dir.mkdir()
    stored = stored_dir / "bundle.zip"
    with zipfile.ZipFile(stored, "w", zipfile.ZIP_STORED) as zf:
        for path in staging.iterdir():
            zf.write(path, "b/%s" % path.name)
    check("an uncompressed zip really does contain raw PEM text",
          b"-----BEGIN CERTIFICATE-----" in stored.read_bytes())
    check("but it is not mistaken for a certificate",
          tls_support.scan_bundle(stored_dir) == [],
          tls_support.scan_bundle(stored_dir))
    check("and nothing is served from it",
          tls_support.locate("install.example.com",
                             cert_dir=str(stored_dir)) is None)

    # Renewing is the same command again with a newer bundle, which is the
    # shape this has to hold: the new certificate serves, the old one is
    # kept but never chosen.
    print("")
    print("== renewing over an installed certificate ==")
    renew = work / "renew-certs"
    renew.mkdir()

    def make_bundle(tag, days):
        src = work / ("renew-src-" + tag)
        src.mkdir()
        cert, key = issue(work, ca_cert, ca_key, "renew.example.com",
                          ["renew.example.com"], days=days)
        # issue() reuses one path per name, so take a copy before the next.
        cert_text = cert.read_text()
        (src / "domain.cert.pem").write_text(cert_text)
        (src / "private.key.pem").write_text(key.read_text())
        archive = renew / ("bundle-%s.zip" % tag)
        with zipfile.ZipFile(archive, "w") as zf:
            for path in src.iterdir():
                zf.write(path, "b/%s" % path.name)
        return archive, cert_text

    old_zip, old_text = make_bundle("old", 5)
    new_zip, new_text = make_bundle("new", 90)
    check("the two bundles really are different certificates",
          old_text != new_text)

    code = install_cert.main([str(old_zip), "--into", str(renew),
                              "--domain", "renew.example.com"])
    check("the first install succeeds", code == 0, code)
    code = install_cert.main([str(new_zip), "--into", str(renew),
                              "--domain", "renew.example.com"])
    check("installing the renewal over it succeeds", code == 0, code)

    installed = (renew / "fullchain.pem").read_text()
    check("the renewed certificate is the one installed",
          new_text.strip() in installed)
    check("the old certificate is gone from it",
          old_text.strip() not in installed)
    check("the old one is kept as a backup",
          old_text.strip() in (renew / "fullchain.pem.1").read_text())
    check("the renewed certificate loads with its own key",
          tls_support.key_matches_cert(str(renew / "fullchain.pem"),
                                       str(renew / "privkey.pem"))[0])
    chosen = tls_support.locate("renew.example.com", cert_dir=str(renew))
    chosen_info = tls_support.inspect(chosen["cert"]) if chosen else {}
    check("the server would serve the renewed one, not the backup",
          bool(chosen)
          and new_text.strip() in Path(chosen["cert"]).read_text(),
          chosen)
    check("and it is the long-dated one",
          isinstance(chosen_info.get("days_left"), int)
          and chosen_info["days_left"] > 30, chosen_info.get("days_left"))
    check("both bundle zips are ignored by the search",
          len(tls_support.scan_bundle(renew)) == 1,
          [Path(p["cert"]).name for p in tls_support.scan_bundle(renew)])

    # A zip that tries to write outside the destination is refused.
    evil = work / "evil.zip"
    with zipfile.ZipFile(evil, "w") as zf:
        zf.writestr("../escaped.pem", "nope")
    try:
        install_cert.unpack(evil, work / "unpack-here")
        check("a zip that escapes its folder is refused", False,
              "it was allowed")
    except ValueError:
        check("a zip that escapes its folder is refused", True)
    check("and nothing was written outside",
          not (work / "escaped.pem").exists())
    print("")


def main() -> int:
    if not shutil.which("openssl"):
        print("tlstests: openssl is not on PATH; these tests need it to mint "
              "throwaway certificates.")
        return 1
    work = Path(tempfile.mkdtemp(prefix="blockhaven-tlstests-"))
    # config reads this at import time, so it has to be set before app.config
    # is first touched -- otherwise the tests would read the real certs/.
    os.environ["BLOCKHAVEN_CERT_DIR"] = str(work / "certs-empty")
    (work / "certs-empty").mkdir(parents=True, exist_ok=True)
    try:
        from app.http import tls
        ca_cert, ca_key = make_ca(work)
        test_name_matching(tls)
        test_discovery(tls, work, ca_cert, ca_key)
        test_chain_assembly(tls, work, ca_cert, ca_key)
        test_rejections(tls, work, ca_cert, ca_key)
        test_locate(tls, work, ca_cert, ca_key)
        test_installer(work, ca_cert, ca_key)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("=" * 60)
    print("  %d passed, %d failed" % (len(PASSED), len(FAILED)))
    if FAILED:
        for name in FAILED:
            print("    FAILED  %s" % name)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
