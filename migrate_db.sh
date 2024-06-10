#!bin/bash

# check if the -m argument is passed
if [ "$1" == "-m" ]; then
    # check if the message is passed
    if [ -z "$2" ]; then
        echo "Please provide a message for the migration"
    else
        # run the migration
        # create the flask migration folder to track the migration versions
        # Note: This is only done once and if the docker container and the volume is destroyed, this will be lost
        # flask db init
        flask db migrate -m "$2"
        flask db upgrade
        echo "Migration successful"
    fi
else
    echo "Please provide a message for the migration"
fi