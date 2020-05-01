FROM hashicorp/terraform:light

WORKDIR /staging

RUN apk add bash

ADD gcp-terraform.contained.sh /app/

VOLUME /project
VOLUME /root/.terraform

ENTRYPOINT ["/app/gcp-terraform.contained.sh"]
