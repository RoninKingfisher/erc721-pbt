#! /bin/bash

export PYTHONPATH=$(dirname $0)

usage() {
  echo "Usage:"
  echo "  $(basename $0) [options] test1 ... testn"
  echo "Options:"
  echo "  -a <arg> : set number of Ethereum accounts"
  echo "  -c <arg> : set stateful step count"
  echo "  -n <arg> : set maximum examples"
  echo "  -s <arg> : set seed for tests"
  echo "  -t <arg> : set number of ERC-721 tokens"
  echo "  -C       : measure coverage"
  echo "  -D       : enable debug output"
  echo "  -E       : enable verification of events"
  echo "  -R       : enable verification of return values"
  echo "  -S       : enable shrinking"
}

PBT_ACCOUNTS=4
PBT_DEBUG=no
PBT_MAX_EXAMPLES=10
PBT_SEED=0
PBT_STATEFUL_STEP_COUNT=5
PBT_TOKENS=6
PBT_PROFILE=generate
PBT_VERIFY_EVENTS=no
PBT_VERIFY_RETURN_VALUES=no
coverage_setting=''

while getopts "a:c:n:s:t:CDERS" options; do
  case "${options}" in  
    a) 
      PBT_ACCOUNTS=${OPTARG}
      ;;
    c)
      PBT_STATEFUL_STEP_COUNT=${OPTARG}
      ;;
    n) 
      PBT_MAX_EXAMPLES=${OPTARG}
      ;;
    s)
      PBT_SEED=${OPTARG}
      ;;
    t) 
      PBT_TOKENS=${OPTARG}
      ;;
    C)
      coverage_setting="--coverage"
      ;;
    D)
      PBT_DEBUG=yes
      ;;
    E)
      PBT_VERIFY_EVENTS=yes
      ;;
    R)
      PBT_VERIFY_RETURN_VALUES=yes
      ;;
    S) 
      PBT_PROFILE="shrinking"
      ;;
    :)
      echo "Error: -${OPTARG} requires an argument."
      usage
      exit 1
      ;;

    *)
      echo Invalid arguments!
      usage
      exit 1
      ;;
  esac
done

shift $(expr $OPTIND - 1 )

if [ "$#" -eq 0 ]; then
  echo No tests specified for execution!
  usage
  exit 1
fi
echo --- Environment variables set --

export PBT_ACCOUNTS \
       PBT_DEBUG \
       PBT_MAX_EXAMPLES \
       PBT_PROFILE \
       PBT_SEED \
       PBT_STATEFUL_STEP_COUNT \
       PBT_TOKENS \
       PBT_VERIFY_EVENTS \
       PBT_VERIFY_RETURN_VALUES

env | grep ^PBT_ | sort 

extra_args=''

if [ "$PBT_DEBUG" == "yes" ]; then
  extra_args="-s"
fi

echo --- Running tests ---
pytest --hypothesis-profile=$PBT_PROFILE $* $extra_args $coverage_setting
