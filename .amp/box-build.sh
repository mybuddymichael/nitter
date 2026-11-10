#!/usr/bin/env bash
set -euo pipefail

# Build on Linux x64 with Nim 2.2, libpcre3-dev, libsass-dev, make, and a C compiler.
export PATH="$HOME/.nimble/bin:$PATH"
nimble --nim:"$(command -v nim)" -y -l build -d:danger --mm:refc
nimble --nim:"$(command -v nim)" -y -l scss
nimble --nim:"$(command -v nim)" -y -l md

# Ship Redis with the release rather than installing a second system-wide service.
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT
curl --fail --silent --show-error --location \
    https://download.redis.io/releases/redis-7.2.17.tar.gz \
    --output "$build_dir/redis.tar.gz"
echo "07c679c013fd82513299733bddf91999bbbc830351ec9ea985a533b09a595d76  $build_dir/redis.tar.gz" | sha256sum --check
tar -xzf "$build_dir/redis.tar.gz" -C "$build_dir"
make -C "$build_dir/redis-7.2.17" -j2 MALLOC=libc BUILD_TLS=no REDIS_CFLAGS= REDIS_LDFLAGS= redis-server
mkdir -p box-runtime
cp "$build_dir/redis-7.2.17/src/redis-server" box-runtime/
cp "$build_dir/redis-7.2.17/COPYING" box-runtime/REDIS-LICENSE

# Diagnose saved sessions on the Box without installing a compiler there.
nim c -d:release --mm:refc --path:src --out:box-runtime/test-sessions tools/test_sessions.nim

# Nim loads PCRE dynamically. The Box provides glibc, OpenSSL, and Python.
cp -L "$(gcc -print-file-name=libpcre.so.3)" box-runtime/libpcre.so.3
cp /usr/share/doc/libpcre3/copyright box-runtime/PCRE-LICENSE
