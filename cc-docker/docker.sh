#!/bin/sh
# output is written to file, process runs in foreground so container doesn't terminate
news-please-cc /npdata/warcs /npdata/articles keep 32 >> /npdata/all.log 2>&1
