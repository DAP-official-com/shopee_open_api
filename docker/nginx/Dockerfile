
ARG NODE_IMAGE_TAG=14-bullseye-slim
ARG DOCKER_REGISTRY_PREFIX=frappe
ARG IMAGE_TAG=develop
FROM node:${NODE_IMAGE_TAG} as builder


ARG GIT_REPO=git@git.arterypartner.com:artery/ap-application/shopee_open_api.git
ARG GIT_BRANCH=version-13

ARG FRAPPE_BRANCH=version-13
ARG ERPNEXT_BRANCH=version-13

# ANCHOR Update linux package & install Requirement lib
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    python2 \
    git \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ANCHOR Copy install application script as shell script 
# NOTE Copy install_frappe.sh in build directory and update linux package
COPY ./docker/nginx/install_frappe.sh /install_frappe
COPY ./docker/nginx/install_app.sh /install_app
COPY ./docker/nginx/prepare_production.sh /prepare_production


# ANCHOR Run install script to install app with change install script
# to executable mode
RUN chmod +x /install_app && \
  chmod +x /install_frappe && \
  chmod +x /prepare_production && \
  # Install frappe
  /install_frappe ${FRAPPE_BRANCH} && \
  # Install apps
  /install_app shopee_open_api ${GIT_REPO} ${GIT_BRANCH} ${FRAPPE_BRANCH} && \
  # Cleanup for production
  /prepare_production

FROM frappe/erpnext-nginx:${ERPNEXT_BRANCH}
# NOTE To Use Private Registry Image use command below
# FROM ${DOCKER_REGISTRY_PREFIX}/frappe-nginx:${IMAGE_TAG}


COPY --from=builder /home/frappe/frappe-bench/sites/ /var/www/html/
COPY --from=builder /rsync /rsync

# Append list of installed to apps.txt
RUN echo -n "shopee_open_api" >> /var/www/html/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"
