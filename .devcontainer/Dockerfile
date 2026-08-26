FROM mcr.microsoft.com/devcontainers/python:1-3.13-bookworm

RUN rm -f /etc/apt/sources.list.d/yarn.list

COPY install-tools.sh /tmp/install-tools.sh

RUN chmod +x /tmp/install-tools.sh \
	&& /tmp/install-tools.sh \
	&& rm /tmp/install-tools.sh
