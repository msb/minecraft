# get the Minecraft pod name
POD=$(kubectl get pod --field-selector=status.phase=Running | sed 's/ .*//' | tail -1)
# create a timestamp for the zip file name
TIMESTAMP=$(date "+%Y%m%d-%H%M")
# zip the world in the container (to minimize chance of corruption)
kubectl exec -it $POD -- zip -r /tmp/mc.$TIMESTAMP.zip /data/worlds
# download the backup..
kubectl cp $POD:/tmp/mc.$TIMESTAMP.zip /tmp/mc.$TIMESTAMP.zip
# ..and upload it to the backup bucket
gsutil cp /tmp/mc.$TIMESTAMP.zip gs://world-backup-98d65a  # TODO get the bucket from TF outputs
# delete the zip from the container
kubectl exec -it $POD -- rm /tmp/mc.$TIMESTAMP.zip