FROM lsiobase/alpine.python

EXPOSE  6767
VOLUME /bazarr/data /tv

# Update
RUN apk add --update build-base python-dev py2-pip py-setuptools jpeg-dev zlib-dev git

WORKDIR /bazarr

# Get application source from Github
RUN git init
RUN git remote add origin https://github.com/morpheus65535/bazarr.git
RUN git fetch
RUN git reset origin/master  # this is required if files in the non-empty directory are in the repo
RUN git checkout -t origin/master
#RUN git clone -b master --single-branch https://github.com/morpheus65535/bazarr.git /bazarr

RUN ls /
RUN ls /bazarr

# Install app dependencies
RUN pip install -r /bazarr/requirements.txt

CMD ["python", "bazarr.py"]