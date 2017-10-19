FROM lsiobase/alpine.python

EXPOSE  6767
VOLUME /tv

# Update
RUN apk add --update build-base python-dev py2-pip py-setuptools jpeg-dev zlib-dev git

ADD . /bazarr

# Install app dependencies
RUN pip install -r /bazarr/requirements.txt

#RUN git clone -b development --single-branch https://github.com/morpheus65535/bazarr.git

WORKDIR /bazarr

CMD ["python", "bazarr.py"]