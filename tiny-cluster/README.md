The project contains terraform configuration for the creation of a
[GCP](https://cloud.google.com) kubernetes cluster. The cluster is configured with only a single
small node and so isn't actually a cluster. However, it is inexpensive to run and would be useful
for:

- running non-mission critical applications
- learning to maintain aspects of a cluster

Before you can create a cluster you will need to create
[a GCP project](https://cloud.google.com/storage/docs/projects) to contain it. A container has been
developed to help with this and instructions for it's use can be found in
[`..\create-gcp-project\README.md`](https://github.com/msb/minecraft/blob/master/create-gcp-project/README.md)
~~TODO update when available on Docker Hub~~. When you have done this a `$PROJECT_CONTAINER`
variable should be defined naming the container with the service account credentials for the
project.

Another container has been developed on top of the standard terraform container to:

- pre-configure terraform with these credentials. 
- configure terraform to store it's state in a 
  [GCP Storage Bucket](https://cloud.google.com/storage/docs/creating-buckets)

Standard terraform commands can be run with this container using a helper script as follows:

```sh
./gcp-terraform.sh $PROJECT_CONTAINER ...
```

Those familiar with [terraform](https://www.terraform.io/docs/index.html) will know that the 1st
command you always need to run is `init`:

```sh
./gcp-terraform.sh $PROJECT_CONTAINER init
```

When initialised, you can create the cluster as follows:

```sh
./gcp-terraform.sh $PROJECT_CONTAINER apply
```

This will take a few minutes to complete. If you have been successful you should see a cluster in
[the console](https://console.cloud.google.com/kubernetes/list), the next thing is to configure
`kubectl` with the new cluster so that you can deploy applications to it. Before you do this you
need to define a file with some variables to be used by `kubectl`:

```sh
CLUSTER_NAME=$(./gcp-terraform.sh $PROJECT_CONTAINER output cluster_name)
CLUSTER_ZONE=$(./gcp-terraform.sh $PROJECT_CONTAINER output cluster_zone)
PROJECT_ID=$(./gcp-terraform.sh $PROJECT_CONTAINER output project_id)

cat <<EOF >kube.env
CLUSTER_NAME=$(echo $CLUSTER_NAME | tr -d '[:space:]')
CLUSTER_ZONE=$(echo $CLUSTER_ZONE | tr -d '[:space:]')
CLOUDSDK_CONFIG=/root/.config/$(echo $PROJECT_ID | tr -d '[:space:]')
EOF
```

Then you can use the [`google/cloud-sdk` container](https://hub.docker.com/r/google/cloud-sdk) to
run `kubectl`:

```sh
# TODO capture this in a script
docker run -it --rm --env-file kube.env --volumes-from=$PROJECT_CONTAINER google/cloud-sdk bash
```

Once in the container, configure `kubectl` with the new cluster:

```sh
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$CLUSTER_ZONE
```

You should now be able to execute `kubectl` commands:

```sh
kubectl cluster-info
```

When it comes to deleting the cluster, you can do this by running:

```sh
./gcp-terraform.sh $PROJECT_CONTAINER destroy
```
