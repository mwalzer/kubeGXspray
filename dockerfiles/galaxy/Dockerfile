FROM ubuntu:14.04
MAINTAINER walzer@ebi.ac.uk

LABEL Description="Galaxy 17.09-basic for running inside Kubernetes."
LABEL software="Galaxy"
LABEL software.version="17.09-basic"
LABEL version="1.0"

RUN apt-get -qq update && apt-get install --no-install-recommends -y apt-transport-https software-properties-common wget && \
    apt-get update -qq && \
    apt-get install --no-install-recommends -y mercurial python-psycopg2 sudo python-virtualenv \
    libyaml-dev libffi-dev libssl-dev \
    curl git python-pip python-gnuplot python-psutil && \
    pip install --upgrade pip && \
    apt-get purge -y software-properties-common && \
    apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN git clone --depth 1 --single-branch --branch v17.09 https://github.com/galaxyproject/galaxy.git

WORKDIR galaxy
RUN echo "pykube==0.15.0" >> requirements.txt
RUN pip install pulsar-galaxy-lib==0.8.3
RUN sed -i 's/pulsar-galaxy-lib==0.8.0//' requirements.txt
#monkeypatch pulsar-galaxy-lib==0.8.0 (pypi py2 only) --> fixed in Feb pulsar-galaxy-lib==0.8.3
#RUN sed -i 's/pulsar-galaxy-lib==0.8.0/pulsar-galaxy-lib==0.8.3/' requirements.txt
#seems to be unavailable
#RUN pip install git+https://github.com/galaxyproject/pulsar.git@0.8.3

COPY config/galaxy.ini config/galaxy.ini
COPY config/job_conf.xml config/job_conf.xml
COPY config/tool_conf.xml config/tool_conf.xml
COPY config/sanitize_whitelist.txt config/sanitize_whitelist.txt
COPY config/datatypes_conf.xml config/datatypes_conf.xml

#COPY tools/phenomenal tools/phenomenal
#COPY ansible ansible
#COPY workflows workflows
#RUN chmod u+x /galaxy/ansible/run_galaxy_config.sh
# Missing XCMS datatypes for w4m
#COPY external-datatypes/rdata_xcms_datatype.py /galaxy/lib/galaxy/datatypes/
#COPY external-datatypes/rdata_camera_datatype.py /galaxy/lib/galaxy/datatypes/
#COPY external-datatypes/no_unzip_datatypes.py /galaxy/lib/galaxy/datatypes/
#COPY external-datatypes/nmrml_datatype.py /galaxy/lib/galaxy/datatypes/

RUN virtualenv .venv
RUN /bin/bash -c "source .venv/bin/activate && \
                  pip install 'pip>=8.1' && \
                  pip install -r requirements.txt \
                      --index-url https://wheels.galaxyproject.org/simple && \
                  deactivate"

# Galaxy runs on python < 3.5, so https://github.com/kelproject/pykube/issues/29 recommends
ENV PYKUBE_KUBERNETES_SERVICE_HOST kubernetes

EXPOSE 8080

CMD ["./run.sh"]
