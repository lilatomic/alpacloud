FROM	alpine:3.20
RUN	apk add build-base alpine-sdk sudo
RUN	adduser -D packager && \
	addgroup packager abuild && \
	echo 'packager ALL=(ALL) NOPASSWD:ALL' >/etc/sudoers.d/packager

RUN apk add bash linux-headers rustup protoc unzip

USER packager
RUN	rustup-init -y
ENV	PATH=$PATH:$HOME/.cargo/bin
WORKDIR /home/packager/
