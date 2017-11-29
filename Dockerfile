FROM lsiobase/alpine:3.6

VOLUME /tv
VOLUME /config

RUN apk add --update git python2 py-pip py-pygit2 jpeg-dev && \
    apk add --update --virtual build-dependencies g++ python-dev libffi-dev zlib-dev  && \
    git clone -b master --single-branch https://github.com/morpheus65535/bazarr.git /app && \
    pip install -r /app/requirements.txt && \
    apk del --purge build-dependencies

COPY root /

LABEL MAINTAINER="peter.varsanyi@gwelican.eu"
LABEL org.label-schema.vcs-ref=$VCS_REF org.label-schema.build-date=$BUILD_DATE

EXPOSE 6767