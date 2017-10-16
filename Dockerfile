FROM alpine:latest

# Update
RUN apk add --update python py-pip

# Install app dependencies
RUN pip install -r requirements.txt

EXPOSE  6767
CMD ["python", "/src/bazarr.py"]