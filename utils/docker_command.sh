sudo mkdir -p /opt/esdata
sudo chmod 777 /opt/esdata

docker run -d --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -e "cluster.routing.allocation.disk.threshold_enabled=false" \
  -v /opt/esdata:/usr/share/elasticsearch/data \
  --ulimit memlock=-1:-1 \
  elasticsearch:8.12.0