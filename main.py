import string
import toml, sys, os, nacl.bindings, binascii
from typing import cast
from dotenv import load_dotenv, find_dotenv

def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)


def pubkey(privkey: str) -> str:
    return binascii.b2a_base64(cast(bytes,
                                    nacl.bindings.crypto_scalarmult_base(
                                        binascii.a2b_base64(privkey))),
                               newline=False).decode('ascii')


def get_peers() -> dict:
    return toml.load(PEERS_FILE)


def make_configs(peers: dict):
    with open("network.template") as tn:
        network_template = string.Template(tn.read())
        tn.close()

    with open("netdev.template") as td:
        netdev_template = string.Template(td.read())
        tn.close()

    for node, details in peers.items():
        output_dir = OUTPUT + node
        mkdir(output_dir)
        a_id = details['id']
        a_pkey = details['private_key']
        a_ipv4 = details['ipv4']
        a_ipv6 = details['ipv6']
        a_only_support_ipv4 = (a_ipv6 == "")
        for peer, connection in peers.items():
            if peer == node:
                continue
            b_pubkey = pubkey(connection['private_key'])
            b_ipv4 = connection['ipv4']
            b_ipv6 = connection['ipv6']
            if a_only_support_ipv4:
                b_endpoint = b_ipv4
            else:
                b_endpoint = b_ipv6
            if b_ipv6 == "" and b_ipv4 != "":
                b_endpoint = b_ipv4
            elif b_ipv6 == "" and b_ipv4 == "":
                b_endpoint = "127.0.0.1"

            dev = DEV_PREFIX + peer

            ndev_output = netdev_template.safe_substitute(
                dev=dev,
                mtu=MTU,
                listen_port=BASE_PORT + connection['id'],
                private_key=a_pkey,
                pubkey=b_pubkey,
                hostname=b_endpoint,
                endpoint_port=BASE_PORT + a_id
            )

            nwork_output = network_template.safe_substitute(
                dev=dev,
                ipv4_prefix=IPV4_PREFIX,
                ipv6_prefix=IPV6_PREFIX,
                id=a_id,
                peer_id=connection["id"]
            )

            with open(output_dir + '/' + dev + ".netdev", "w") as od:
                od.write(ndev_output)
                od.close()

            with open(output_dir + '/' + dev + ".network", "w") as ow:
                ow.write(nwork_output)
                ow.close()

if __name__ == '__main__':
    global BASE_PORT, DEV_PREFIX, MTU, PEERS_FILE, OUTPUT, IPV4_PREFIX, IPV6_PREFIX
    load_dotenv(verbose=True)
    BASE_PORT = os.getenv("BASE_PORT")
    DEV_PREFIX = os.getenv("DEV_PREFIX")
    MTU = os.getenv("MTU")
    PEERS_FILE = os.getenv("PEERS_FILE")
    OUTPUT = os.getenv("OUTPUT")
    IPV4_PREFIX = os.getenv("IPV4_PREFIX")
    IPV6_PREFIX = os.getenv("IPV6_PREFIX")
    peers = get_peers()
    make_configs(peers)
