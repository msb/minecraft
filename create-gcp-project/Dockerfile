FROM google/cloud-sdk

WORKDIR /app

ADD create-gcp-project.contained.sh ./

VOLUME /root/.project

ENTRYPOINT ["./create-gcp-project.contained.sh"]
