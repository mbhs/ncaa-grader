git pull

old_container=$(docker ps -a -q  --filter ancestor=ncaa)

old_image=$(docker images -q ncaa)

#docker rm $(docker stop $(docker ps -a -q  --filter ancestor=mbhs))

docker build . -t ncaa --no-cache

docker stop $old_container

docker run --restart unless-stopped -d -p 3009:80 ncaa

docker rm $old_container

docker rmi $old_image
