if [[ -z $1 || -z $2 ]]; then
  echo usage: $0 [location:dallas,atlanta,fremont,london,newark,tokyo] [payment-term:1,12,24]
  exit 1
fi

KEY_NAME=deis-controller
KEY_PATH=~/.ssh/$KEY_NAME
KEY_PUB=~/.ssh/$KEY_NAME.pub

if [ ! -f $KEY_PATH ] ; then
  echo "Creating new SSH key: $KEY_NAME"
  ssh-keygen -f $KEY_PATH -t rsa -N '' -C "deis-controller" >/dev/null
  echo "Saved to $KEY_PATH"
else
  echo "Using SSH key $KEY_PUB"
fi

IP=""

function linode_ip {
	if [ "$IP" == "" ]; then
		echo  "Grabbing IP address of new node.."

		IP=`linode show $NAME | grep ips | awk '{print $2}'`
	fi
}

NAME="deis-controller-$(LC_CTYPE=C tr -dc A-Za-z0-9 < /dev/urandom | head -c 5 | xargs)"

if [ $NAME = 'deis-controller-' ]; then
  echo "Couldn't generate unique name for deis-controller. Aborting."
  exit 1
fi

SSH=`cat $KEY_PUB`
JSON="{\"ssh_key\":\"$SSH\"}"

if [ ! -z $3 ]; then
	NAME=$3
	echo "Rebuilding an existing linode ($3)"

	linode rebuild $NAME -S 8511 -J "$JSON"

	if [ $? -ne 0 ]; then
		echo "There was a problem rebuilding the linode."
		exit
	fi

	echo "Delete client name from chef"

	knife client delete $NAME

	linode_ip

	echo "Remove old accepted SSH host keys"

	ssh-keygen -R $IP
else
	linode create $NAME \
	  --location $1 \
	  --plan linode2048 \
	  --payment-term $2 \
	  --stackscript 8511 \
	  --stackscriptjson "$JSON"

	if [ $? -ne 0 ]; then
		echo "There was a problem creating the linode."
		exit
	fi
fi

echo -ne "Wait for linode to launch..."

while : ; do
	STATUS=`linode show $NAME | grep status | awk '{print $2}'`

	echo -ne "."

	[ "$STATUS" != "running" ] || break
done

echo "Running"

echo -ne "Grabbing IP address of new node.."

IP=`linode show $NAME | grep ips | awk '{print $2}'`

echo $IP

echo -ne "Wait for linode to finish executing StackScript (this will take about 10 minutes)..."

sleep 30 # stack script installs SSH key, so wait a bit for it to do its job

while : ; do
	RUNNING=`ssh -o LogLevel=quiet -o "StrictHostKeyChecking no" -i ~/.ssh/deis-controller root@$IP  'ps -ef | grep StackScript | grep -v grep | wc -l'`

	echo -ne "."

	[ "$RUNNING" == "1" ] || break
done

echo "Complete"

echo "Provisiong node with chef:"

knife bootstrap $IP \
  bootstrap-version 11.8.2 \
  ssh-user root \
  --sudo \
  --node-name $NAME \
  --identity-file $KEY_PATH\
  --json-attributes "{\"docker\":{\"storage_driver\":\"devicemapper\"}}" \
  --run-list "recipe[deis::controller]"

<<comment
CONTROLLERUP=0

echo -ne "Wait for controller to respond..."

while [ $CONTROLLERUP -eq 0 ]; do
	echo -ne "."

	curl http://$nodeip:8000 >/dev/null 2>&1;

	if [ $? -eq 0 ]; then
		CONTROLLERUP = 1
	else
		sleep 10
	fi
done
comment