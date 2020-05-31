# Wrapper script to put us into the cluster management container.

docker run -it --rm -e HISTFILE=/cluster/.bash_history \
  -v minecraft-cluster:/cluster -v $PWD:/minecraft google/cloud-sdk bash
