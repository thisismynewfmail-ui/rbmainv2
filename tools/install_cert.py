#!/usr/bin/env python3
"""Install a TLS certificate so the site can serve HTTPS.

Registrars and hosts hand out a zip -- Porkbun, Namecheap, cPanel, ZeroSSL,
all of them -- and every one of them names the files differently.  This takes
the zip (or the folder it was unpacked into, or the two files themselves),
works out which file is which, checks the things that silently make a browser
say "Not secure", and writes the result into ``certs/`` under the two names
certbot uses::

    python3 tools/install_cert.py ~/Downloads/example.com-ssl-bundle.zip
    python3 tools/install_cert.py ./example.com-ssl-bundle/
    python3 tools/install_cert.py --cert domain.cert.pem --key private.key.pem

After that ``./run.sh`` finds it with no flags at all.

What gets checked, because each of these is invisible until a visitor hits it:

* the private key really belongs to the certificate,
* the chain is complete and leaf-first -- a desktop browser hides a missing
  intermediate by fetching it, a phone does not,
* the certificate has not expired and is not post-dated,
* the name it covers is the name the site is reached by.

Nothing is overwritten destructively: an existing certificate is rolled to
``fullchain.pem.1`` first, so a bad renewal can be undone by hand.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional, Tuple

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from app import config                      # noqa: E402
from app.http import tls as tls_support     # noqa: E402

CERT_NAME = "fullchain.pem"
KEY_NAME = "privkey.pem"
KEEP_OLD = 5
# A certificate bundle is a few kilobytes of text.  Anything claiming to be
# much more is not one, and unpacking it to find out is how a zip bomb wins.
MAX_UNPACKED_BYTES = 8 * 1024 * 1024
MAX_ZIP_ENTRIES = 200


def fail(message: str) -> int:
    print("install_cert: %s" % message, file=sys.stderr)
    return 1


# ------------------------------------------------------------------- unpack
def unpack(archive: Path, into: Path) -> None:
    """Extract ``archive`` into ``into``, refusing anything that escapes it.

    ``ZipFile.extractall`` follows ``../`` and absolute paths in member names,
    which is how a downloaded archive gets to write outside the directory it
    was pointed at.  Every member is resolved against the destination first.
    """
    with zipfile.ZipFile(archive) as zf:
        members = zf.infolist()
        if len(members) > MAX_ZIP_ENTRIES:
            raise ValueError("%s holds %d files; that is not a certificate "
                             "bundle" % (archive.name, len(members)))
        total = sum(max(0, info.file_size) for info in members)
        if total > MAX_UNPACKED_BYTES:
            raise ValueError("%s unpacks to %.1f MB; that is not a certificate "
                             "bundle" % (archive.name, total / 1048576.0))
        root = into.resolve()
        for info in members:
            if info.is_dir():
                continue
            target = (root / info.filename).resolve()
            if not str(target).startswith(str(root) + os.sep):
                raise ValueError("%s contains a path that escapes the "
                                 "destination: %s" % (archive.name,
                                                      info.filename))
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst, 65536)


# -------------------------------------------------------------------- write
def roll(path: Path) -> None:
    """Shuffle ``path`` down to ``path.1``, ``.1`` to ``.2``, and so on."""
    if not path.exists():
        return
    for index in range(KEEP_OLD, 0, -1):
        older = path.with_name(path.name + ".%d" % index)
        if index == KEEP_OLD and older.exists():
            older.unlink()
            continue
        if older.exists():
            older.rename(path.with_name(path.name + ".%d" % (index + 1)))
    path.rename(path.with_name(path.name + ".1"))


def _owner() -> Optional[Tuple[int, int]]:
    """The account that called sudo, so the files stay theirs to read.

    ``sudo ./run.sh`` binds as root and then serves as the calling user, and
    the certificate is read before that hand-over -- but ``./run.sh --port
    8972`` never becomes root at all, and a root-owned 0600 key would stop it
    dead.  Writing the files as the real user keeps both ways of starting the
    server working.
    """
    user = os.environ.get("SUDO_USER", "")
    if not user or os.geteuid() != 0:
        return None
    try:
        import pwd
        entry = pwd.getpwnam(user)
    except (ImportError, KeyError):
        return None
    return entry.pw_uid, entry.pw_gid


def write(path: Path, text: str, mode: int, owner: Optional[Tuple[int, int]]) -> None:
    roll(path)
    # The key is written through a 0600 handle rather than chmod-ed after the
    # fact, so it is never briefly readable by everybody on the machine.
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.chmod(path, mode)
    if owner:
        try:
            os.chown(path, owner[0], owner[1])
        except OSError:
            pass


# --------------------------------------------------------------------- main
def _note_leftover_source(args, destination: Path) -> None:
    """The download is a copy of the private key; say where it ended up.

    Installing does not delete what it was given -- nobody wants a tool that
    removes the file they pointed it at -- so the next best thing is to be
    plain about what is still lying around and whether git can see it.
    """
    if not args.source:
        return
    try:
        source = Path(args.source).expanduser().resolve()
    except OSError:
        return
    if not source.is_file():
        return
    try:
        source.relative_to(destination.resolve())
        inside_certs = True
    except (ValueError, OSError):
        inside_certs = False
    try:
        source.relative_to(config.BASE_DIR)
        inside_project = True
    except ValueError:
        inside_project = False

    # Only the project's own certs/ is the one .gitignore covers; --into
    # can point anywhere, and promising that an arbitrary folder is ignored
    # would be exactly the wrong thing to be confident about.
    is_default_certs = inside_certs and destination.resolve() == \
        config.CERT_DIR.resolve()

    print("  %s holds your private key as well." % source.name)
    if is_default_certs:
        print("  It is in %s/, which .gitignore covers, so it will not be "
              "committed." % config.CERT_DIR.name)
        print("  Delete it once the site is serving HTTPS.")
    elif inside_project:
        print("  It is inside the project folder, and only %s/ is gitignored."
              % config.CERT_DIR.name)
        print("  Move it out or delete it, so it cannot be committed by "
              "accident.")
    else:
        print("  Delete it once the site is serving HTTPS.")
    print("")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install a TLS certificate into %s/"
                    % config.CERT_DIR.name,
        epilog="With no arguments, an already-installed certificate is "
               "re-checked.")
    parser.add_argument("source", nargs="?", default="",
                        help="the bundle: a .zip, or the folder it was "
                             "unpacked into")
    parser.add_argument("--cert", default="",
                        help="the certificate file, if naming it directly")
    parser.add_argument("--key", default="",
                        help="the private key file, if naming it directly")
    parser.add_argument("--chain", default="",
                        help="the intermediate certificates, when they are "
                             "in a file of their own")
    parser.add_argument("--into", default=str(config.CERT_DIR),
                        help="where to install (default: %s)"
                             % config.CERT_DIR)
    parser.add_argument("--domain", default=config.DOMAIN,
                        help="the name the site is served as, to confirm the "
                             "certificate covers it")
    parser.add_argument("--force", action="store_true",
                        help="install even when a check fails (an expired "
                             "certificate, a name that does not match)")
    args = parser.parse_args(argv)

    if not args.source and not args.cert and not args.key:
        usable, text = tls_support.report(args.domain, cert_dir=args.into)
        print(text)
        if not usable:
            # The commonest way to be here is having put the download in
            # certs/ and stopped, so finish the sentence rather than
            # repeating the generic advice.
            for archive in sorted(Path(args.into).glob("*.zip")):
                print("")
                print("%s is sitting there un-installed. This will do it:"
                      % archive.name)
                print("  python3 tools/install_cert.py %s" % archive)
                break
        return 0 if usable else 1

    destination = Path(args.into).expanduser()
    staging = Path(tempfile.mkdtemp(prefix="blockhaven-cert-"))
    try:
        return _install(args, destination, staging)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def _install(args, destination: Path, staging: Path) -> int:
    cert = args.cert
    key = args.key
    chain = args.chain

    if not (cert and key):
        source = Path(args.source).expanduser()
        if not source.exists():
            return fail("no such file or folder: %s" % source)
        if source.is_file() and zipfile.is_zipfile(source):
            print("unpacking %s" % source.name)
            try:
                unpack(source, staging)
            except (ValueError, zipfile.BadZipFile, OSError) as exc:
                return fail(str(exc))
            search = staging
        elif source.is_dir():
            search = source
        else:
            return fail("%s is neither a zip nor a folder. Name the two "
                        "files directly with --cert and --key if they are "
                        "loose." % source)

        pairs = tls_support.scan_bundle(search)
        if not pairs:
            return fail(
                "no certificate and matching private key in %s.\n"
                "            Found: %s\n"
                "            A bundle normally holds a certificate "
                "(domain.cert.pem, certificate.crt, fullchain.pem ...) and "
                "the key\n            it was issued against "
                "(private.key.pem, privkey.pem ...). public.key.pem is not "
                "the private key."
                % (source, ", ".join(sorted(p.name for p in search.rglob("*")
                                            if p.is_file())) or "nothing"))
        cert, key, chain = pairs[0]["cert"], pairs[0]["key"], pairs[0]["chain"]
        if len(pairs) > 1:
            print("note: %d certificates in there; using %s"
                  % (len(pairs), Path(cert).name))

    verdict = tls_support.evaluate({"cert": cert, "key": key, "chain": chain},
                                   args.domain)
    info = verdict.get("info") or {}
    print("")
    print("  certificate  %s" % cert)
    print("  private key  %s" % key)
    if chain:
        print("  chain        %s" % chain)
    if isinstance(info, dict):
        if info.get("names"):
            print("  covers       %s" % ", ".join(str(n) for n in info["names"]))
        if info.get("issuer"):
            print("  issued by    %s" % info["issuer"])
        if info.get("expires"):
            days = info.get("days_left")
            print("  expires      %s%s"
                  % (info["expires"],
                     "  (%d days)" % days if isinstance(days, int) else ""))
        if info.get("count"):
            count = int(info["count"])
            print("  chain depth  %d certificate%s"
                  % (count, "" if count == 1 else "s"))
    if verdict.get("chain_note"):
        print("  fixed up     %s" % verdict["chain_note"])
    print("")

    for warning in verdict.get("warnings") or []:
        print("  note:    %s" % warning)
    problems = verdict.get("problems") or []
    for problem in problems:
        print("  PROBLEM: %s" % problem)
    if problems and not args.force:
        print("")
        return fail("not installing. Pass --force to install it anyway.")

    serve_cert = Path(str(verdict.get("serve_cert") or cert))
    try:
        cert_text = serve_cert.read_text("utf-8", "replace")
        key_text = Path(key).read_text("utf-8", "replace")
    except OSError as exc:
        return fail("could not read the files: %s" % exc)

    owner = _owner()
    replacing = (destination / CERT_NAME).exists()
    try:
        destination.mkdir(parents=True, exist_ok=True)
        os.chmod(destination, 0o755)
        if owner:
            try:
                os.chown(destination, owner[0], owner[1])
            except OSError:
                pass
        write(destination / CERT_NAME, cert_text, 0o644, owner)
        write(destination / KEY_NAME, key_text, 0o600, owner)
    except PermissionError:
        return fail("cannot write into %s as this user.\n"
                    "            Either run it with sudo, or hand the folder "
                    "back:\n"
                    "              sudo chown -R $USER %s"
                    % (destination, destination))
    except OSError as exc:
        return fail("could not write into %s: %s" % (destination, exc))

    ok, why = tls_support.key_matches_cert(str(destination / CERT_NAME),
                                           str(destination / KEY_NAME))
    if not ok:
        return fail("the installed pair does not load: %s" % why)

    print("  installed    %s" % (destination / CERT_NAME))
    print("               %s  (mode 600)" % (destination / KEY_NAME))
    if replacing:
        # Renewing is the same command as installing, so say which one this
        # was -- and where the one it replaced went, since that is the only
        # copy left if the new certificate turns out to be wrong.
        print("  replaced     the certificate that was already there")
        print("               (kept as %s.1 and %s.1)" % (CERT_NAME, KEY_NAME))
        print("               Restart the server to pick this one up.")
    print("")
    _note_leftover_source(args, destination)
    name = ""
    if isinstance(info, dict) and info.get("names"):
        name = tls_support.primary_name([str(n) for n in info["names"]],
                                        args.domain)
    print("Start the site and it will be found:")
    print("  sudo ./run.sh")
    if name:
        print("  then open https://%s" % name)
    print("")
    print("  ./run.sh --tls-check      says what is in use and what is not")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
