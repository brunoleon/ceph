#!/bin/bash
set -x
WORKUNITS_DIR=$CEPH_BASE/qa/workunits
sudo $WORKUNITS_DIR/deepsea/health-ok.sh --profile=bs_dedicated_wal_db_sizes_all
