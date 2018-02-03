## Build fusesoc-img
# docker build  -t fusesoc-img  .
## Run tests in container and bolt.
# docker run  --rm -it  -v $PWD:/fusesoc fusesoc-img
## Run container with bash terminal for manual debugging
# docker run  --rm -it  -v $PWD:/fusesoc fusesoc-img  -c /bin/bash

FROM ubuntu:latest
RUN apt-get update
RUN apt-get install -y git man python python-pip  python-setuptools subversion vim wget curl

WORKDIR /fusesoc

CMD ["-c","pip install -e .;py.test;rm -rf tests/cache tests/__pycache__"]
ENTRYPOINT ["/bin/bash"]
