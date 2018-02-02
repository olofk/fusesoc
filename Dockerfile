# docker build  -t fusesoc-img  .
# docker run  --rm -it  -v $PWD:/fusesoc fusesoc-img  -c "pip install -e .;py.test"

FROM ubuntu:latest
RUN apt-get update
RUN apt-get install -y git man python python-pip  python-setuptools subversion vim wget curl

WORKDIR /fusesoc
ENTRYPOINT ["/bin/bash"]
