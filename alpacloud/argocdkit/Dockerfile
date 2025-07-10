# -------- Stage 1: Build Helm --------
FROM	debian:bullseye AS helm-installer

ARG	HELM_URL="https://get.helm.sh/helm-v3.18.3-linux-amd64.tar.gz"
ARG	HELM_SHA256="6ec85f306dd8fe9eb05c61ba4593182b2afcfefb52f21add3fe043ebbdc48e39"

RUN	apt-get update && apt-get install -y --no-install-recommends \
	curl \
	ca-certificates \
	tar \
	coreutils \
	&& rm -rf /var/lib/apt/lists/*

RUN	set -eux && \
	mkdir -p /tmp/helm && cd /tmp/helm && \
	curl -sSL "$HELM_URL" -o helm.tar.gz && \
	echo "$HELM_SHA256  helm.tar.gz" | sha256sum -c - && \
	tar -zxvf helm.tar.gz && \
	mv linux-amd64/helm /helm && \
	chmod +x /helm

# -------- Stage 2: Final Python Image --------
FROM	python:3.13-slim

COPY	--from=helm-installer /helm /usr/local/bin/helm
COPY	alpacloud.argocdkit/__main__.pex /bin/alpacloud-argocdkit
RUN	/bin/alpacloud-argocdkit gen-cfg

COPY	alpacloud.argocdkit.test_resources/my_postrenderer.pex /bin/my_postrenderer
