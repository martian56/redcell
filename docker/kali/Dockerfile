# REDCELL execution image: Kali base with a curated pentest toolset baked in.
# Published to Docker Hub as martian56/kali:latest so any host (local or a remote
# server) can pull it. Rebuild + push with:
#     docker build -t martian56/kali:latest docker/kali && docker push martian56/kali:latest
#   Full Kali headless metapackage (huge, ~6-8 GB, slow):
#     docker build --build-arg FULL=1 -t martian56/kali:latest docker/kali
#
# The platform default (Settings -> Local execution image) is martian56/kali:latest;
# the engine runs every command inside a container of it, local or remote.
FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

ARG FULL=0
RUN apt-get update && apt-get install -y --no-install-recommends \
      # basics
      ca-certificates curl wget git jq vim less \
      netcat-traditional socat openssh-client \
      dnsutils iputils-ping net-tools \
      python3 python3-pip python3-venv \
      # network / recon
      nmap masscan \
      subfinder amass dnsrecon whatweb \
      # web
      sqlmap nikto wpscan \
      gobuster ffuf feroxbuster dirb dirbuster \
      nuclei httpx-toolkit \
      # exploitation / creds
      hydra john hashcat \
      # wordlists
      seclists wordlists \
 && if [ "$FULL" = "1" ]; then apt-get install -y --no-install-recommends kali-linux-headless; fi \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# rockyou ships gzipped; unpack it so tools can use it directly.
RUN [ -f /usr/share/wordlists/rockyou.txt.gz ] && gunzip -f /usr/share/wordlists/rockyou.txt.gz || true

WORKDIR /root
CMD ["sleep", "infinity"]
