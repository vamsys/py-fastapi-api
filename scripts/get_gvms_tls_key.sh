#!/usr/bin/env bash
set -euo pipefail

cd "$HOME"

if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
fi

read -r -p "Enter number: " number

read -r -p "Enter blue or green: " color

read -r -p "Enter ingress or egress (default: ingress): " traffic
traffic="${traffic:-ingress}"

if [ "$traffic" != "ingress" ] && [ "$traffic" != "egress" ]; then
	echo "ERROR: traffic must be 'ingress' or 'egress' (got '$traffic')." >&2
	exit 1
fi

output="$({
    klsit "$number" 2>&1
	klconfig "GVMS-sit-${color}" 2>&1
	
})"

printf '%s\n' "$output"

run_date="$(date +%Y%m%d)"
key_file="sit-${traffic}-${run_date}.key"
pem_file="sit-${traffic}-${run_date}.pem"

kubectl get secret "gvms-${traffic}-tls" -n gvms -ojson | jq -r '.data["tls.key"]' | base64 -d > "$key_file"
kubectl get secret "gvms-${traffic}-tls" -n gvms -ojson | jq -r '.data["tls.crt"]' | base64 -d > "$pem_file"

if [ ! -s "$key_file" ]; then
	echo "ERROR: Expected file '$key_file' was not created (or is empty)." >&2
	exit 1
fi

if [ ! -s "$pem_file" ]; then
	echo "ERROR: Expected file '$pem_file' was not created (or is empty)." >&2
	exit 1
fi

p12_file="tKs-${traffic}-${run_date}.p12"
echo "Creating '$p12_file' using password 'changeit'"
openssl pkcs12 -export -in "$pem_file" -inkey "$key_file" -certfile "$pem_file" -out "$p12_file" -passout pass:changeit

if [ ! -s "$p12_file" ]; then
	echo "ERROR: Expected file '$p12_file' was not created (or is empty)." >&2
	exit 1
fi

jks_file="sit-${traffic}-${run_date}.jks"
echo "Converting '$p12_file' to '$jks_file' using password 'changeit'"
keytool -importkeystore \
	-srckeystore "$p12_file" \
	-srcstoretype pkcs12 \
	-srcstorepass changeit \
	-destkeystore "$jks_file" \
	-deststoretype JKS \
	-deststorepass changeit \
	-noprompt

if [ ! -s "$jks_file" ]; then
	echo "ERROR: Expected file '$jks_file' was not created (or is empty)." >&2
	exit 1
fi






