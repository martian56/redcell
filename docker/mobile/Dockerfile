ARG KALI_VERSION=1.0.0
FROM ghcr.io/martian56/redcell-kali:${KALI_VERSION}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      default-jre-headless \
      unzip \
      apktool \
      dex2jar \
      aapt \
      apksigner \
      libplist-utils \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

ARG JADX_VERSION=1.5.1
RUN curl -fsSL "https://github.com/skylot/jadx/releases/download/v${JADX_VERSION}/jadx-${JADX_VERSION}.zip" -o /tmp/jadx.zip \
 && unzip -q /tmp/jadx.zip -d /opt/jadx \
 && rm /tmp/jadx.zip \
 && ln -s /opt/jadx/bin/jadx /usr/local/bin/jadx \
 && ln -s /opt/jadx/bin/jadx-gui /usr/local/bin/jadx-gui

RUN pip3 install --no-cache-dir --break-system-packages apkleaks

WORKDIR /root
CMD ["sleep", "infinity"]
