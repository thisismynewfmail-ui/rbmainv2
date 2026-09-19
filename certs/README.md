# certs/

Put the certificate for the site here and `./run.sh` serves HTTPS with no
flags at all. **Nothing in this folder is committed** — `.gitignore` keeps
every key, certificate and archive out of the repository, and it has to stay
that way: a private key in a git history is a compromised private key, even
after the commit that added it is deleted.

## Installing a certificate

Registrars and hosts hand out a zip (Porkbun, Namecheap, cPanel, ZeroSSL and
friends all do). Unpack it here with the installer, which checks it over
before it writes anything:

```
python3 tools/install_cert.py ~/Downloads/example.com-ssl-bundle.zip
sudo ./run.sh
```

The installer takes a zip, a folder, or the files themselves:

```
python3 tools/install_cert.py ./example.com-ssl-bundle/
python3 tools/install_cert.py --cert domain.cert.pem --key private.key.pem
```

It normalises whatever it is given to two files — `fullchain.pem` and
`privkey.pem`, the names certbot uses — assembling the chain from a separate
intermediate file and re-ordering it leaf-first if the download was not.

## Checking one

```
./run.sh --tls-check
```

lists every certificate found, what each covers, when it expires, and why any
of them were passed over. That is the first thing to run when a browser says
"Not secure".

## What the server accepts

Any of these layouts is recognised, at this level or one or two folders down,
so an unpacked bundle works where it landed:

| what           | names it is known by                                         |
|----------------|--------------------------------------------------------------|
| certificate    | `fullchain.pem`, `domain.cert.pem`, `certificate.crt`, `cert.pem`, `server.crt`, … |
| private key    | `privkey.pem`, `private.key.pem`, `private.key`, `server.key`, … |
| intermediates  | `intermediate.cert.pem`, `chain.pem`, `ca_bundle.crt`, …      |

Names only decide what is tried first. Files are classified by what is in
them, so a bundle whose provider invented its own names is still found — and
`public.key.pem`, which ships in most bundles and is not a private key, is
ignored rather than tried.

A certbot certificate under `/etc/letsencrypt/live/<domain>/` is still picked
up as before; nothing here replaces that.

## Renewing

Drop the new bundle in and restart:

```
python3 tools/install_cert.py ~/Downloads/example.com-ssl-bundle.zip
sudo systemctl restart blockhaven     # or however this is run
```

The old files are kept as `fullchain.pem.1`, `privkey.pem.1` and so on, so a
bad renewal can be backed out by hand.
