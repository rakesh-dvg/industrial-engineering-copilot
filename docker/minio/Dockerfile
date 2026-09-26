# Official MinIO Community Edition built from source.
# Docker Hub minio/minio was removed; Quay anonymous pulls are disabled on this network.

FROM golang:1.24-alpine AS build

ARG RELEASE=RELEASE.2025-09-07T16-13-09Z

RUN apk add --no-cache git ca-certificates

WORKDIR /src
RUN git clone --depth 1 --branch "${RELEASE}" https://github.com/minio/minio.git . \
    && CGO_ENABLED=0 go build -trimpath -o /minio .

FROM alpine:3.20

RUN apk add --no-cache ca-certificates curl

COPY --from=build /minio /usr/bin/minio

EXPOSE 9000 9001

ENTRYPOINT ["/usr/bin/minio"]
