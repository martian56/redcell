# Kali execution image. The engine runs every command inside a container of this,
# so it ships with the pentest tools an engagement actually reaches for.
# Published as martian56/kali:latest so any host can pull it:
#     docker build -t martian56/kali:latest docker/kali && docker push martian56/kali:latest
# Pass FULL=1 for the kali-linux-headless metapackage (~6-8 GB, slow build):
#     docker build --build-arg FULL=1 -t martian56/kali:latest docker/kali
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
      # browser automation (agent-driven + live VNC view)
      chromium xvfb x11vnc \
      # exploitation / creds
      hydra john hashcat \
      # wordlists
      seclists wordlists \
 && if [ "$FULL" = "1" ]; then apt-get install -y --no-install-recommends kali-linux-headless; fi \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# rockyou ships gzipped; unpack it so tools can use it directly.
RUN [ -f /usr/share/wordlists/rockyou.txt.gz ] && gunzip -f /usr/share/wordlists/rockyou.txt.gz || true

# Playwright as a CDP client only (drives the apt chromium above), so no browser
# download is needed. Kali's Python is externally managed, hence --break-system-packages.
RUN pip3 install --no-cache-dir --break-system-packages playwright

# Agent-driven browser helper + supervisor.
COPY rc-browserd rc-browser /usr/local/bin/
RUN chmod +x /usr/local/bin/rc-browserd /usr/local/bin/rc-browser

WORKDIR /root
CMD ["sleep", "infinity"]
