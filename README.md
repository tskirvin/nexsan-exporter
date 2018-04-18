nexsan-exporter
===============

Allows probing of Nexsan arrays by [Prometheus](https://prometheus.io/).
Modelled after the [Blackbox
exporter](https://github.com/prometheus/blackbox_exporter).

[![Build Status](https://travis-ci.org/yrro/nexsan-exporter.svg?branch=master)](https://travis-ci.org/yrro/nexsan-exporter)

Running
-------

```
$ python3 -m pip install git+https://github.com/yrro/nexsan.git
$ nexsan-exporter
```

You can then visit <http://localhost:9333/probe?target=192.0.2.1&user=foo&pass=bar> to view
metrics for the target device; for instance:

```
# HELP nexsan_... description
# TYPE nexsan_... gauge
nexsan_... 0
```

The following labels are used:

 * `label`: description
 * `label`: description
 * `label`: description

Packaging
---------

To produce a Debian package:

```
$ debian/rules clean
$ dpkg-buildpackage -b
```

The `prometheus-nexsan-exporter` package will be created in the parent directory.

Prometheus configuration
------------------------

Something like the following:

```yaml
scrape_configs:
 - job_name: nexsan
   metrics_path: /probe
   static_configs:
    - targets:
        - 192.0.2.1
   relabel_configs:
    - source_labels: [__address__]
      target_label: __param_target
    - source_labels: [__param_target]
      target_label: instance
    - target_label: __address__
      replacement: exporter-host:9333
```

Exporter Configuration
----------------------

Some useful options can be given to `exporter.py` on the command line.

```
$ nexsan-exporter
usage: nexsan-exporter [-h] [--bind-address BIND_ADDRESS] [--bind-port BIND_PORT]
                       [--bind-v6only {0,1}] [--thread-count THREAD_COUNT]

optional arguments:
  -h, --help            show this help message and exit
  --bind-address BIND_ADDRESS
                        IPv6 or IPv4 address to listen on
  --bind-port BIND_PORT
                        Port to listen on
  --bind-v6only {0,1}   If 1, prevent IPv6 sockets from accepting IPv4
                        connections; if 0, allow; if unspecified, use OS
                        default
  --thread-count THREAD_COUNT
                        Number of request-handling threads to spawn
```

Development
-----------

I'm trying to keep things simple and rely only on the Python standard library
and the [prometheus_client](https://github.com/prometheus/client_python)
module.

To fetch and install dependencies and run `exporter` from source:

```
$ python3 -m pip install -e .
$ nexsan-exporter
```

or, without installing:


```
$ python3 -m nexsan_exporter
```
