build:
	podman load --input="$(shell nom build '.#url-shortener.container' --print-out-paths)"

run: build
	podman run -it --rm -p 8000:8000/tcp --name url-shortener pw/url-shortener:latest
