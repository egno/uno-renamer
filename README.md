# build

docker build -t renamer .

# run

docker run -it --rm -v /opt/data/images:/opt/data/images renamer

# cron

/usr/bin/docker run -it --rm -v /opt/data/images:/opt/data/images renamer 

