# Connect to instance.
gcloud compute ssh --zone $ZONE --project $PROJECT $INSTANCE

# 1. Copy code

gcloud compute scp --zone $ZONE --project $PROJECT --recurse * $INSTANCE:~/autoinvest/
gcloud compute scp --zone $ZONE --project $PROJECT --recurse .secrets $INSTANCE:~/autoinvest/
# Run `chmod 0700 .secrets` on the machine!

# 2. Install dependencies

./install_packages.sh
