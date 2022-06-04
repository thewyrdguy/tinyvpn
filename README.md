# Tiny and simple VPN implementation for educational purposes

The sole purpose of this code is to demonstrate prinicples of operation
of a point to point VPN. Traffic in the tunnel is not encrypted, and
the source of the traffic is not check in any way, even by the source
IP address. It does not perform address assignment nor install any
routes in the system. It is not suitable for "real use".

The code in Python opens a UDP socket and binds it to the specified
port. It also creates a TUN interface with specified name, and proceeds
to copy data between the TUN character device and the socket, using
specified address of the peer to send UDP packets.

The code is rather short and hopefully reasonably easy to understand,
which is the purpose of this work.

## Running the program

The program must be run as root. Start it like this:

```
# tinyvpn.py [-d] interface-name peer-host-name-or-addr port
```

`-d` option selects verbose output. Every sent and received packet
is printed to stdout.

`interface-name` is the name of the TUN interface that will be created.
Value "stdio" has a special meaning: instead of creating the interface,
lines read from stdin are sent to the tunnel, and UDP datagrams received
from the tunnel are output to stdout. The program operates similar to
`netcat` in UDP mode. This mode does not require root permissions; it
may be useful to test that the tunnel is operational before engaging
the VPN mode.

`peer-host-name-or-addr` is the address of the peer. This value is used
only as the destination address for sending UDP packets. The source of
received packets can be any (it is even possible to deliver traffic
in one direction over IPv4, and in the other - over IPv6).

`port` is the UDP port to use _both_ to bind the socket and as the
destination port in the sent packets. It must be set to the same
value on both sides.

## How to use (test) the program

* On two hosts (real or virtual machines) that have IP connectivity
  between them run the program, specifying the name or address of
  the peer host, and using the same port number on both hosts.
* Chose an IP network of the size of at least /30 that is not used
  on any of the hosts. Chose two addresses for the two hosts.
* Assuming that the interface name was set to "`testvpn`", and
  chosen addresses were `10.10.10.1/30` and `10.10.10.2/30`,
  configure the interface on both hosts:

  ```
  # ip link set testvpn up
  # ip address add 10.10.10.1/30 dev testvpn
  ```

  on one of the hosts, and

  ```
  # ip link set testvpn up
  # ip address add 10.10.10.2/30 dev testvpn
  ```

  on the other.
* Enjoy connectivity between these addresses. You can ping the peer's
  address, ssh to it, etc.

## License and Copyright

Copyright (c) 2022 Peter Wyrd `<thewyrdguy@gmail.com>`

Released under MIT license
