#!/usr/bin/env bash
# 関数定義
function cleanup {
    echo "Exiting program."
    exit 0
}
# Ctrl-C で cleanup 関数を呼び出すように設定
trap cleanup INT
while true
do
#    echo "Getting Data..."
#    python3 /root/a.py > /run/a.csv; mv /run/a.csv /root/src/taiwan_$(date +%Y_%m_%d_%H_%M_%S).csv
    python3 /root/oreno_mabiki.py
    sleep 5
#    echo "Getting Data... done."
done
