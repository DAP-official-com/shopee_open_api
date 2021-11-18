ARG ERPNEXT_BRANCH=version-13
FROM frappe/erpnext-worker:${ERPNEXT_BRANCH}
COPY . /home/frappe/frappe-bench/apps/shopee_open_api

USER root 
RUN chown frappe:frappe -R /home/frappe/frappe-bench/apps
USER frappe

RUN /home/frappe/frappe-bench/env/bin/pip3 install -e /home/frappe/frappe-bench/apps/shopee_open_api
