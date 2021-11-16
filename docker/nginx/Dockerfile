ARG FRAPPE_BRANCH=version-13
ARG ERPNEXT_BRANCH=version-13
FROM node:14-buster
ARG FRAPPE_BRANCH=version-13
ARG ERPNEXT_BRANCH=version-13

COPY ./docker/nginx/install_frappe.sh /install_frappe
COPY ./docker/nginx/install_app.sh /install_app
COPY ./docker/nginx/prepare_production.sh /prepare_production
COPY . /home/frappe/frappe-bench/apps/audit_documents
COPY ./repos/castlecraft /home/frappe/frappe-bench/apps/castlecraft

# Install frappe
RUN /install_frappe ${FRAPPE_BRANCH} && \
  # Install apps
  /install_app castlecraft && \
  /install_app audit_documents && \
  # Cleanup for production
  /prepare_production

FROM frappe/erpnext-nginx:${ERPNEXT_BRANCH}

COPY --from=0 /home/frappe/frappe-bench/sites/ /var/www/html/
COPY --from=0 /rsync /rsync

# Append list of installed to apps.txt
RUN echo -n "castlecraft\naudit_documents" >> /var/www/html/apps.txt

VOLUME [ "/assets" ]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"
