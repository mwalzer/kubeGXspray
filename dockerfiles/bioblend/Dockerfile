FROM alpine:latest
MAINTAINER Mathias Walzer <walzer@ebi.ac.uk>

RUN apk add --update python py-pip && \
    pip install bioblend && \
    rm -rf /var/cache/apk/*  && \
    rm -rf /var/lib/{cache,log} && \
    rm -rf /tmp/* && \
    rm -rf /var/tmp/* 

