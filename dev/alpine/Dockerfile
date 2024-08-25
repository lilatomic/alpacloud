FROM	alpine:3.20
RUN	apk add build-base alpine-sdk sudo
RUN	adduser -D packager && \
	addgroup packager abuild && \
	echo 'packager ALL=(ALL) NOPASSWD:ALL' >/etc/sudoers.d/packager

USER packager
WORKDIR /home/packager/
