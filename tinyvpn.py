#!/usr/bin/env python3

from fcntl import ioctl
from getopt import getopt
from ipaddress import ip_address, IPv6Address
from os import set_blocking
from select import poll, POLLIN
from socket import getaddrinfo, socket, AF_INET6, SOCK_DGRAM
from struct import pack
from sys import argv, stdin, stdout


def run(debug_mode, ifname, sockaddr):
    # First, open UDP socket
    netsock = socket(AF_INET6, SOCK_DGRAM)
    # And bind it to the specified port
    netsock.bind(("::", sockaddr[1]))

    # next take care of the tun interface, or use stdin/stdout
    if ifname == "stdio":  # for debugging, just act as `netcat` command
        if debug_mode:
            print("using stdin/stdout as the end of the tunnel")
        tunin = stdin.buffer.raw
        tunout = stdout.buffer.raw
    else:
        if debug_mode:
            print(f"using interface {ifname} as the end of the tunnel")
        TUNSETIFF = 0x400454CA
        IFF_TUN = 0x0001
        IFF_NO_PI = 0x1000
        # Create tun interface with specified name
        tunin = open("/dev/net/tun", "r+b", buffering=0)
        ifr = pack("16sH", ifname.encode(), IFF_TUN | IFF_NO_PI)
        ioctl(tunin, TUNSETIFF, ifr)
        tunout = tunin  # Separate only for compatibility with stdio

    # Now prepare the poll object (ignore possible write stalls)
    pollset = poll()
    tunfd = tunin.fileno()
    set_blocking(tunfd, False)
    netfd = netsock.fileno()
    pollset.register(tunfd, POLLIN)
    pollset.register(netfd, POLLIN)

    # And run infinite loop, passing data between file descriptors
    while True:
        try:
            events = pollset.poll()
            if debug_mode:
                print(f"poll returned events {events}")
        except KeyboardInterrupt:
            break
        for fd, ev in events:
            if fd == tunfd:
                data = tunin.read()
                if debug_mode:
                    print("got data from tun:", data)
                netsock.sendto(data, sockaddr)
            elif fd == netfd:
                data, peer_addr = netsock.recvfrom(1500)
                if debug_mode:
                    print("got data from", peer_addr, ":", data)
                try:
                    tunout.write(data)
                except OSError as e:
                    if debug_mode:
                        print(f"writing to tun: {e}, ignoring")
            else:
                raise RuntimeError(f"Unexpected event {ev} on fd {fd}")

    # Broken from the `while True` loop
    pollset.unregister(tunfd)
    pollset.unregister(netfd)
    netsock.close()
    tunin.close()
    tunout.close()


if __name__ == "__main__":
    topts, args = getopt(argv[1:], "d")
    opts = dict(topts)
    debug_mode = "-d" in opts
    if debug_mode:
        print("running", argv[0], "with opts", opts, "and args", args)
    try:
        ifname, host, port = args
    except ValueError:
        print(f"usage: {argv[0]} [-d] {{ifname|stdio}} peer-host port")
        raise
    for fam, typ, pro, cnm, skadr in getaddrinfo(host, port, type=SOCK_DGRAM):
        break  # Just take the first element
    if len(skadr) < 4:  # we were given an IPv4 address, convert it!
        addr6 = IPv6Address(0xFFFF << 32 | int(ip_address(skadr[0])))
        for fam, typ, pro, cnm, sockaddr in getaddrinfo(
            str(addr6), port, type=SOCK_DGRAM
        ):
            break
    else:
        sockaddr = skadr
    run(debug_mode, ifname, sockaddr)
