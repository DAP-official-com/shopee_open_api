ARG IMAGE_TAG=develop
ARG DOCKER_REGISTRY_PREFIX=frappe

FROM ${DOCKER_REGISTRY_PREFIX}/frappe-worker:${IMAGE_TAG}

COPY . /home/frappe/frappe-bench/apps/shopee_open_api

USER root 
RUN chown frappe:frappe -R /home/frappe/frappe-bench/apps

USER frappe
RUN /home/frappe/frappe-bench/env/bin/pip3 install -e /home/frappe/frappe-bench/apps/shopee_open_api
