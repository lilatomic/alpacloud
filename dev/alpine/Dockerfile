FROM	alpine:3.20
RUN	apk add build-base~=0.5 alpine-sdk~=1.0 sudo~=1.9 --no-cache
RUN	adduser -D packager && \
	addgroup packager abuild && \
	echo 'packager ALL=(ALL) NOPASSWD:ALL' >/etc/sudoers.d/packager

RUN apk add bash~=5.2 linux-headers=~6.6 rustup=~1.25 protoc~=24.4 unzip~=6.0 --no-cache

USER packager
RUN	rustup-init -y
ENV	PATH=$PATH:$HOME/.cargo/bin
WORKDIR /home/packager/
